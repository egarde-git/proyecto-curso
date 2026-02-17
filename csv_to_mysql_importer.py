import os
import csv
import shutil
import argparse
import logging
import subprocess
import sys
import importlib

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_and_install_dependencies():
    """Valida e instala las dependencias necesarias de forma automática."""
    dependencies = [
        ("pymysql", "pymysql"),
        ("cryptography", "cryptography")
    ]

    for package, module in dependencies:
        try:
            importlib.import_module(module)
        except ImportError:
            logger.info(
                f"Dependencia faltante detectada: '{package}'. Intentando instalar...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package])
                logger.info(
                    f"Dependencia '{package}' instalada correctamente.")
            except subprocess.CalledProcessError as e:
                logger.critical(
                    f"Error crítico al instalar '{package}'. Asegúrate de tener pip instalado y conexión a internet. Detalles: {e}")
                sys.exit(1)
            except Exception as e:
                logger.critical(
                    f"Error inesperado instalando '{package}': {e}")
                sys.exit(1)


# Instalar dependencias antes de importar
check_and_install_dependencies()

import pymysql
from pymysql import Error


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Importar archivos CSV de ofertas a MySQL.')

    parser.add_argument('--host', required=True,
                        help='Host de la base de datos MySQL')
    parser.add_argument('--port', required=True,
                        help='Puerto de la base de datos MySQL')
    parser.add_argument('--user', required=True,
                        help='Usuario de la base de datos MySQL')
    parser.add_argument('--password', required=True,
                        help='Contraseña de la base de datos MySQL')
    parser.add_argument('--database', required=True,
                        help='Nombre de la base de datos')
    parser.add_argument('--csv_dir', required=True,
                        help='Directorio donde se encuentran los archivos CSV')

    return parser.parse_args()


def create_connection(host_name, port, user_name, user_password, db_name):
    connection = None
    try:
        connection = pymysql.connect(
            host=host_name,
            port=int(port),
            user=user_name,
            password=user_password,
            database=db_name
        )
        logger.info("Conexión a la base de datos MySQL exitosa.")
    except Error as e:
        logger.error(f"Error al conectar a la base de datos '{db_name}': {e}")
        raise
    return connection


def create_table_if_not_exists(connection):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS ofertas (
        ensenya VARCHAR(50),
        timestamp DATETIME,
        postal_code CHAR(10),
        id VARCHAR(100),
        name VARCHAR(255),
        price DECIMAL(10,2),
        is_on_promotion BOOL,
        url VARCHAR(2048),
        image_file VARCHAR(255),
        category_name_1 VARCHAR(255),
        category_id_1 VARCHAR(100),
        category_name_2 VARCHAR(255),
        category_id_2 VARCHAR(100),
        category_name_3 VARCHAR(255),
        category_id_3 VARCHAR(100),
        category_name_4 VARCHAR(255),
        category_id_4 VARCHAR(100),
        category_name_5 VARCHAR(255),
        category_id_5 VARCHAR(100),
        brand VARCHAR(255),
        ean VARCHAR(50),
        promotion_1 VARCHAR(255),
        promotion_2 VARCHAR(255)
    );
    """
    cursor = connection.cursor()
    try:
        cursor.execute(create_table_query)
        logger.info("Verificación/Creación de tabla 'ofertas' completada.")
    except Error as e:
        logger.error(f"Error al crear la tabla: {e}")
        raise
    finally:
        cursor.close()


def get_ensenya_from_filename(filename):
    # Asume formato: nombre_resto.csv -> nombre
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    if parts:
        return parts[0]
    return 'unknown'


def move_to_processed(file_path, processed_dir):
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        logger.info(f"Directorio creado: {processed_dir}")

    file_name = os.path.basename(file_path)
    destination = os.path.join(processed_dir, file_name)

    try:
        # Si el archivo ya existe en destino, shutil.move puede fallar o sobrescribir dependiendo del SO
        # Aquí lo movemos directamente
        if os.path.exists(destination):
            # Opcional: eliminar si ya existe para reemplazar
            os.remove(destination)

        shutil.move(file_path, destination)
        logger.info(f"Archivo movido a: {destination}")
    except Exception as e:
        logger.error(f"Error al mover el archivo {file_name}: {e}")


def import_csv_file(connection, file_path, processed_dir):
    logger.info(f"Iniciando importación del archivo: {file_path}")

    ensenya = get_ensenya_from_filename(file_path)
    rows_to_insert = []

    # Definir la consulta SQL
    # Nota: Asumimos que el CSV contiene columnas que mapean a los campos excepto 'ensenya'
    # Ajustaremos esto leyendo el header del CSV

    sql_insert_query = """
    INSERT INTO ofertas (
        ensenya, timestamp, postal_code, id, name, price, is_on_promotion, url, image_file,
        category_name_1, category_id_1, category_name_2, category_id_2, 
        category_name_3, category_id_3, category_name_4, category_id_4, 
        category_name_5, category_id_5, brand, ean, promotion_1, promotion_2
    ) VALUES (
        %s,STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i:%%s'),%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,
        %s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s
    )
    """

    try:
        # Usar encoding 'utf-8-sig' para manejar BOM si existe
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csv_file:
            # Leer una muestra para detectar el dialecto (delimitador)
            try:
                sample = csv_file.read(4096)
                csv_file.seek(0)
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                # Si falla (ej. archivo pequeño o formato extraño), usamos defaults
                csv_file.seek(0)
                dialect = 'excel'

            csv_reader = csv.DictReader(csv_file, dialect=dialect)

            # Limpiar espacios en blanco de los nombres de las columnas
            if csv_reader.fieldnames:
                csv_reader.fieldnames = [name.strip()
                                         for name in csv_reader.fieldnames]

            for row in csv_reader:
                # Conversión y limpieza básica de datos

                # Manejo de is_on_promotion (bool)
                is_promo = row.get('is_on_promotion', 'False')
                if isinstance(is_promo, str):
                    is_promo = 1 if is_promo.lower() in ('true', '1', 'yes') else 0

                # Manejo de price (decimal)
                raw_price = row.get('price', '0.0')
                if isinstance(raw_price, str):
                    # Limpiar símbolo de moneda, espacios normales y no separables (\xa0)
                    clean_price = raw_price.replace(
                        '€', '').replace('\xa0', '').replace(' ', '')
                    # Reemplazar coma decimal por punto
                    clean_price = clean_price.replace(',', '.')
                    try:
                        price = float(clean_price)
                    except ValueError:
                        price = 0.0
                else:
                    try:
                        price = float(raw_price)
                    except (ValueError, TypeError):
                        price = 0.0

                # Crear tupla para inserción
                # Asegurarse de usar .get() para evitar KeyErrors si falta alguna columna en el CSV
                data_tuple = (
                    ensenya,
                    row.get('timestamp'),
                    row.get('postal_code'),
                    row.get('id'),
                    row.get('name'),
                    price,
                    is_promo,
                    row.get('url'),
                    row.get('image_file'),
                    row.get('category_name_1'),
                    row.get('category_id_1'),
                    row.get('category_name_2'),
                    row.get('category_id_2'),
                    row.get('category_name_3'),
                    row.get('category_id_3'),
                    row.get('category_name_4'),
                    row.get('category_id_4'),
                    row.get('category_name_5'),
                    row.get('category_id_5'),
                    row.get('brand'),
                    row.get('ean'),
                    row.get('promotion_1'),
                    row.get('promotion_2')
                )
                rows_to_insert.append(data_tuple)

        if rows_to_insert:
            cursor = connection.cursor()
            cursor.executemany(sql_insert_query, rows_to_insert)
            connection.commit()
            logger.info(
                f"Insertadas {cursor.rowcount} filas desde {os.path.basename(file_path)}")
            cursor.close()

            # Mover a procesados solo si la inserción fue exitosa
            move_to_processed(file_path, processed_dir)
        else:
            logger.warning(
                f"El archivo {file_path} está vacío o no contiene datos válidos.")
            # Opcional: mover a procesados si está vacío para no reintentar infinitamente
            move_to_processed(file_path, processed_dir)

    except Error as e:
        logger.error(f"Error de base de datos al importar {file_path}: {e}")
        if connection.open:
            connection.rollback()
    except Exception as e:
        logger.error(f"Error general procesando el archivo {file_path}: {e}")
        if connection.open:
            connection.rollback()


def main():
    logger.info("Iniciando script de importación CSV a MySQL...")

    # 1. & 2. Validar parámetros
    args = parse_arguments()

    # Validar existencia directorio CSV
    if not os.path.exists(args.csv_dir):
        logger.error(
            f"El directorio CSV especificado no existe: {args.csv_dir}")
        return

    connection = None
    try:
        # 3. Conexión a la base de datos
        connection = create_connection(args.host, int(
            args.port), args.user, args.password, args.database)

        # 4. & 5. Comprobar / crear tabla
        create_table_if_not_exists(connection)

        # 7. Definir directorio procesados
        processed_dir = os.path.join(args.csv_dir, '_PROCESSED_FILES')

        # 6. Importar CSVs
        files = [f for f in os.listdir(args.csv_dir) if f.endswith(
            '.csv') and os.path.isfile(os.path.join(args.csv_dir, f))]

        if not files:
            logger.info(
                "No se encontraron archivos CSV para procesar en el directorio.")
        else:
            logger.info(
                f"Se encontraron {len(files)} archivos CSV para procesar.")
            for file_name in files:
                file_path = os.path.join(args.csv_dir, file_name)
                import_csv_file(connection, file_path, processed_dir)

    except Exception as e:
        logger.critical(f"Error crítico en la ejecución del script: {e}")
    finally:
        if connection and connection.open:
            connection.close()
            logger.info("Conexión a la base de datos cerrada.")

    logger.info("Ejecución del script finalizada.")


if __name__ == "__main__":
    main()
