"""
Predictor de Huella CO2
Piloto IA - FICEM BD

Entrena y usa modelos ML para predecir huella de carbono en concretos.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


class HuellaPredictor:
    """
    Predictor de huella de carbono usando Gradient Boosting.
    """

    def __init__(self, model_path: str = None):
        """
        Inicializa el predictor.

        Args:
            model_path: Ruta al modelo guardado. Si no existe, se entrena uno nuevo.
        """
        self.model = None
        self.feature_names = None
        self.stats = {}

        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            print("No se encontro modelo guardado. Se entrenara uno nuevo.")

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara features para el modelo.

        Args:
            df: DataFrame con datos crudos

        Returns:
            DataFrame con features procesadas
        """
        df = df.copy()

        # Rellenar NaNs con 0
        df = df.fillna(0)

        # Features derivadas
        df['intensidad_total_a1_a3'] = df['a1_intensidad'] + df['a2_intensidad'] + df['a3_intensidad']
        df['ratio_a1_total'] = df['a1_intensidad'] / (df['intensidad_total_a1_a3'] + 1e-6)
        df['ratio_a2_total'] = df['a2_intensidad'] / (df['intensidad_total_a1_a3'] + 1e-6)
        df['ratio_a3_total'] = df['a3_intensidad'] / (df['intensidad_total_a1_a3'] + 1e-6)
        df['cemento_por_resistencia'] = df['contenido_cemento'] / (df['resistencia'] + 1)

        # One-hot encoding para compania
        df = pd.get_dummies(df, columns=['compania'], prefix='comp', drop_first=True)

        return df

    def train(self, db_path: str, save_path: str = None):
        """
        Entrena el modelo con datos de la base de datos.

        Args:
            db_path: Ruta a la base de datos SQLite
            save_path: Ruta donde guardar el modelo entrenado
        """
        print("Cargando datos...")
        conn = sqlite3.connect(db_path)

        query = """
        SELECT
            compania,
            año,
            resistencia,
            contenido_cemento,
            a1_intensidad,
            a2_intensidad,
            a3_intensidad,
            a4_intensidad,
            huella_co2
        FROM remitos_concretos
        WHERE huella_co2 > 0 AND resistencia > 0
        """

        df = pd.read_sql_query(query, conn)

        print(f"Datos cargados: {len(df):,} registros")

        # Preparar features
        df = self.prepare_features(df)

        # Definir features
        self.feature_names = [col for col in df.columns if col not in ['huella_co2']]

        X = df[self.feature_names]
        y = df['huella_co2']

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"Entrenando modelo Gradient Boosting...")
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            random_state=42
        )

        self.model.fit(X_train, y_train)

        # Evaluar
        y_pred = self.model.predict(X_test)
        self.stats = {
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred),
            'n_train': len(X_train),
            'n_test': len(X_test)
        }

        print(f"Modelo entrenado!")
        print(f"  R²: {self.stats['r2']:.4f}")
        print(f"  RMSE: {self.stats['rmse']:.2f} kg CO₂/m³")
        print(f"  MAE: {self.stats['mae']:.2f} kg CO₂/m³")

        # Guardar
        if save_path:
            self.save_model(save_path)

    def predict(self, features: dict) -> dict:
        """
        Predice huella de carbono.

        Args:
            features: Diccionario con features {
                'compania': str,
                'año': int,
                'resistencia': float,
                'contenido_cemento': float,
                'a1_intensidad': float,
                'a2_intensidad': float,
                'a3_intensidad': float,
                'a4_intensidad': float
            }

        Returns:
            Diccionario con predicción e intervalo de confianza
        """
        if not self.model:
            raise ValueError("Modelo no inicializado. Entrena o carga un modelo primero.")

        # Crear DataFrame
        df = pd.DataFrame([features])

        # Preparar features
        df = self.prepare_features(df)

        # Asegurar que todas las columnas existen
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0

        # Ordenar columnas
        df = df[self.feature_names]

        # Predecir
        prediccion = self.model.predict(df)[0]

        # Intervalo de confianza aproximado (± 1.96 * MAE)
        ci_lower = max(0, prediccion - 1.96 * self.stats.get('mae', 20))
        ci_upper = prediccion + 1.96 * self.stats.get('mae', 20)

        return {
            'prediccion': round(prediccion, 2),
            'ci_lower': round(ci_lower, 2),
            'ci_upper': round(ci_upper, 2),
            'r2': self.stats.get('r2', 0),
            'rmse': self.stats.get('rmse', 0)
        }

    def save_model(self, path: str):
        """Guarda el modelo entrenado."""
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'stats': self.stats
        }
        joblib.dump(model_data, path)
        print(f"Modelo guardado en: {path}")

    def load_model(self, path: str):
        """Carga un modelo guardado."""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.stats = model_data['stats']
        print(f"Modelo cargado desde: {path}")
        print(f"  R²: {self.stats.get('r2', 0):.4f}")
        print(f"  RMSE: {self.stats.get('rmse', 0):.2f} kg CO₂/m³")


# Script para entrenar y guardar modelo
if __name__ == "__main__":
    DB_PATH = "/home/cpinilla/databases/ficem_bd/data/ficem_bd.db"
    MODEL_PATH = "ai_modules/ml/saved_models/huella_predictor.pkl"

    predictor = HuellaPredictor()
    predictor.train(DB_PATH, MODEL_PATH)

    # Test
    test_features = {
        'compania': 'MZMA',
        'año': 2024,
        'resistencia': 25.0,
        'contenido_cemento': 350.0,
        'a1_intensidad': 0.25,
        'a2_intensidad': 0.02,
        'a3_intensidad': 0.05,
        'a4_intensidad': 0.01
    }

    resultado = predictor.predict(test_features)
    print(f"\nTest de prediccion:")
    print(f"  Prediccion: {resultado['prediccion']} kg CO₂/m³")
    print(f"  IC 95%: [{resultado['ci_lower']}, {resultado['ci_upper']}]")
