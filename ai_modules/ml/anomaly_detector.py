"""
Detector de Anomalías para Huella de Carbono
Piloto IA - FICEM BD

Detecta remitos con huellas de carbono anormales usando Isolation Forest
y análisis estadístico.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
import joblib
from pathlib import Path


class AnomalyDetector:
    """
    Detector de anomalías en datos de huella de carbono.

    Utiliza dos enfoques:
    1. Isolation Forest (detección no supervisada)
    2. Z-score (detección estadística basada en desviaciones)
    """

    def __init__(self, contamination=0.01, z_threshold=3.0):
        """
        Inicializa el detector de anomalías.

        Args:
            contamination: Proporción esperada de anomalías (default: 1%)
            z_threshold: Umbral de Z-score para considerar anomalía (default: 3.0)
        """
        self.contamination = contamination
        self.z_threshold = z_threshold
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.feature_stats = {}
        self.is_fitted = False

    def fit(self, df: pd.DataFrame, features: List[str] = None):
        """
        Entrena el detector con datos históricos.

        Args:
            df: DataFrame con datos históricos
            features: Lista de features a usar. Si None, usa automáticamente.
        """
        if features is None:
            # Features por defecto
            features = [
                'resistencia', 'huella_co2', 'contenido_cemento',
                'a1_intensidad', 'a2_intensidad', 'a3_intensidad'
            ]
            # Filtrar solo las que existen
            features = [f for f in features if f in df.columns]

        self.features = features

        # Preparar datos (eliminar nulos)
        df_clean = df[features].dropna()

        # Calcular estadísticas para Z-score
        for feature in features:
            self.feature_stats[feature] = {
                'mean': df_clean[feature].mean(),
                'std': df_clean[feature].std(),
                'median': df_clean[feature].median(),
                'q1': df_clean[feature].quantile(0.25),
                'q3': df_clean[feature].quantile(0.75),
                'iqr': df_clean[feature].quantile(0.75) - df_clean[feature].quantile(0.25)
            }

        # Escalar datos
        X_scaled = self.scaler.fit_transform(df_clean)

        # Entrenar Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.isolation_forest.fit(X_scaled)

        self.is_fitted = True
        print(f"✅ Detector de anomalías entrenado con {len(df_clean):,} registros")
        print(f"   Features: {', '.join(features)}")
        print(f"   Contaminación esperada: {self.contamination*100:.2f}%")

    def detect(self, df: pd.DataFrame, method='both') -> pd.DataFrame:
        """
        Detecta anomalías en nuevos datos.

        Args:
            df: DataFrame con datos a analizar
            method: Método de detección ('isolation', 'zscore', 'both')

        Returns:
            DataFrame con columnas adicionales:
                - is_anomaly_isolation: bool
                - is_anomaly_zscore: bool
                - is_anomaly: bool (combina ambos métodos)
                - anomaly_score: float
                - anomaly_reason: str
        """
        if not self.is_fitted:
            raise ValueError("Detector no entrenado. Ejecutar fit() primero.")

        df_result = df.copy()

        # Preparar datos
        df_features = df[self.features].copy()

        # Método 1: Isolation Forest
        if method in ['isolation', 'both']:
            # Escalar
            X_scaled = self.scaler.transform(df_features.fillna(df_features.median()))

            # Predecir (-1 = anomalía, 1 = normal)
            predictions_if = self.isolation_forest.predict(X_scaled)
            scores_if = self.isolation_forest.score_samples(X_scaled)

            df_result['is_anomaly_isolation'] = (predictions_if == -1)
            df_result['isolation_score'] = scores_if

        # Método 2: Z-score
        if method in ['zscore', 'both']:
            anomalies_zscore = []
            zscore_max = []

            for idx in df_features.index:
                max_z = 0
                is_anomaly = False

                for feature in self.features:
                    value = df_features.loc[idx, feature]
                    if pd.isna(value):
                        continue

                    mean = self.feature_stats[feature]['mean']
                    std = self.feature_stats[feature]['std']

                    if std > 0:
                        z_score = abs((value - mean) / std)
                        max_z = max(max_z, z_score)

                        if z_score > self.z_threshold:
                            is_anomaly = True

                anomalies_zscore.append(is_anomaly)
                zscore_max.append(max_z)

            df_result['is_anomaly_zscore'] = anomalies_zscore
            df_result['max_zscore'] = zscore_max

        # Combinar métodos
        if method == 'both':
            df_result['is_anomaly'] = (
                df_result['is_anomaly_isolation'] |
                df_result['is_anomaly_zscore']
            )
            # Score combinado (normalizado 0-1, 1 = más anómalo)
            df_result['anomaly_score'] = (
                (1 - (df_result['isolation_score'] - df_result['isolation_score'].min()) /
                 (df_result['isolation_score'].max() - df_result['isolation_score'].min())) * 0.5 +
                (df_result['max_zscore'] / 10).clip(0, 1) * 0.5
            )
        elif method == 'isolation':
            df_result['is_anomaly'] = df_result['is_anomaly_isolation']
            df_result['anomaly_score'] = 1 - (df_result['isolation_score'] - df_result['isolation_score'].min()) / (df_result['isolation_score'].max() - df_result['isolation_score'].min())
        else:  # zscore
            df_result['is_anomaly'] = df_result['is_anomaly_zscore']
            df_result['anomaly_score'] = (df_result['max_zscore'] / 10).clip(0, 1)

        # Identificar razones de anomalía
        df_result['anomaly_reason'] = df_result.apply(
            lambda row: self._get_anomaly_reason(row, df_features.loc[row.name])
            if row['is_anomaly'] else '',
            axis=1
        )

        return df_result

    def _get_anomaly_reason(self, row, features_row) -> str:
        """Identifica la razón de la anomalía"""
        reasons = []

        for feature in self.features:
            value = features_row[feature]
            if pd.isna(value):
                continue

            stats = self.feature_stats[feature]
            z_score = abs((value - stats['mean']) / stats['std']) if stats['std'] > 0 else 0

            if z_score > self.z_threshold:
                if value > stats['mean']:
                    reasons.append(f"{feature} muy alto ({value:.1f} vs {stats['mean']:.1f})")
                else:
                    reasons.append(f"{feature} muy bajo ({value:.1f} vs {stats['mean']:.1f})")

        if not reasons:
            reasons.append("Patrón inusual detectado por Isolation Forest")

        return "; ".join(reasons[:3])  # Máximo 3 razones

    def get_anomalies_summary(self, df_detected: pd.DataFrame) -> Dict:
        """
        Genera un resumen de anomalías detectadas.

        Args:
            df_detected: DataFrame con anomalías detectadas

        Returns:
            Diccionario con estadísticas de anomalías
        """
        total = len(df_detected)
        anomalies = df_detected[df_detected['is_anomaly'] == True]
        num_anomalies = len(anomalies)

        summary = {
            'total_records': total,
            'num_anomalies': num_anomalies,
            'anomaly_rate': num_anomalies / total if total > 0 else 0,
            'avg_huella_normal': df_detected[df_detected['is_anomaly'] == False]['huella_co2'].mean() if 'huella_co2' in df_detected.columns else None,
            'avg_huella_anomalies': anomalies['huella_co2'].mean() if len(anomalies) > 0 and 'huella_co2' in df_detected.columns else None,
            'top_reasons': anomalies['anomaly_reason'].value_counts().head(5).to_dict() if len(anomalies) > 0 else {}
        }

        return summary

    def save(self, path: str):
        """Guarda el detector entrenado"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            'contamination': self.contamination,
            'z_threshold': self.z_threshold,
            'features': self.features,
            'feature_stats': self.feature_stats,
            'isolation_forest': self.isolation_forest,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted
        }

        joblib.dump(state, path)
        print(f"✅ Detector guardado: {path}")

    @classmethod
    def load(cls, path: str):
        """Carga un detector entrenado"""
        state = joblib.load(path)

        detector = cls(
            contamination=state['contamination'],
            z_threshold=state['z_threshold']
        )

        detector.features = state['features']
        detector.feature_stats = state['feature_stats']
        detector.isolation_forest = state['isolation_forest']
        detector.scaler = state['scaler']
        detector.is_fitted = state['is_fitted']

        print(f"✅ Detector cargado: {path}")
        return detector


# Ejemplo de uso
if __name__ == "__main__":
    print("Módulo de detección de anomalías para Piloto IA - FICEM BD")
    print("Uso:")
    print("  from ai_modules.ml.anomaly_detector import AnomalyDetector")
    print("  detector = AnomalyDetector(contamination=0.01)")
    print("  detector.fit(df_historico)")
    print("  df_con_anomalias = detector.detect(df_nuevos)")
