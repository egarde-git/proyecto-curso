> **⚠️ NOTA PARA REVISIÓN**  
> He invitado a **mouredev@gmail.com** como colaborador del repositorio de GitHub para que pueda acceder y revisarlo.

# Descripción general del proyecto

Este proyecto consiste en el desarrollo de una aplicación en Python orientada al **análisis y estudio de retailers online** mediante técnicas de **Web Scraping** y posterior almacenamiento de la información en una **base de datos MySQL**.

La finalidad principal es permitir la realización de **estudios de mercado** sobre diferentes retailers online, analizando aspectos como:

- Surtido de productos
- Precios
- Tipos de promociones
- Diferencias por zona geográfica

Uno de los puntos clave del proyecto es la **zonificación** de la información. Dependiendo del **código postal**, un mismo retailer puede ofrecer diferentes productos, precios o promociones, por lo que la aplicación permite obtener y analizar estos datos de forma segmentada por zonas.

## Funcionamiento general

El proyecto se divide en dos grandes fases:

### 1. Obtención de la información (Web Scraping)

Para cada retailer se desarrolla un **script específico en Python**, encargado de acceder a su página web y extraer la información publicada.

Cada script:
- Accede a la web del retailer correspondiente.
- Establece el **código postal** indicado para obtener la información zonificada.
- Recorre las **categorías y subcategorías** de la web.
- Extrae la información de los productos (surtido, precios, promociones, etc.).
- Guarda la información obtenida en un archivo **CSV**.

Durante el proceso de descarga:
- El archivo se crea inicialmente con extensión `.tmp`.
- A medida que se obtiene información, esta se va escribiendo en el archivo `.tmp`.
- Una vez finalizada la descarga, el archivo se renombra a `.csv`, indicando que el proceso ha finalizado correctamente.

Este proceso se puede ejecutar tantas veces como sea necesario:
- Para diferentes retailers.
- Para diferentes zonas (códigos postales).

### 2. Procesamiento e importación a base de datos

Una vez generados los archivos CSV, un segundo script en Python se encarga de:

- Recorrer todos los CSV disponibles en un directorio.
- Tratar y normalizar la información contenida en ellos.
- Conectarse a una base de datos **MySQL**.
- Comprobar si existe la tabla `ofertas`.
  - Si no existe, el script la crea automáticamente.
- Insertar los datos procesados en la base de datos.

Tras la importación, los archivos CSV se conservan para mantener un **histórico de descargas**, permitiendo análisis posteriores o comparativas temporales.

## Objetivo final

El resultado final del proyecto es una base de datos estructurada y actualizada que permite:

- Analizar el comportamiento de distintos retailers online.
- Comparar surtidos, precios y promociones.
- Estudiar diferencias por zona geográfica.
- Facilitar futuros estudios de mercado y análisis de competencia.

# Stack tecnológico

El proyecto está desarrollado íntegramente en **Python**, utilizando diferentes scripts especializados para cada una de las fases del proceso. El stack tecnológico ha sido elegido con el objetivo de ser **sencillo, mantenible y fácilmente extensible** a nuevos retailers o zonas geográficas.

## Lenguaje de programación

- **Python**
  - Lenguaje principal del proyecto.
  - Utilizado tanto para la obtención de datos mediante Web Scraping como para el procesamiento e importación de la información.
  - Permite un desarrollo rápido, claro y con gran disponibilidad de librerías para scraping y acceso a bases de datos.

## Web Scraping

- **Scripts independientes por retailer**
  - Cada retailer tiene su propio script de scraping (por ejemplo: `dia_scraper.py`, `consum_scraper.py`).
  - Esto permite adaptar la lógica de obtención de datos a las particularidades de cada web.
  - Los scripts reciben parámetros de ejecución para indicar:
    - Código Postal (zonificación).
    - Ruta de salida de los archivos CSV.

- **Extracción de información**
  - Establecimiento del código postal en la web del retailer.
  - Recorrido de categorías y subcategorías.
  - Obtención de información de productos, precios y promociones.
  - Generación de archivos CSV como resultado del proceso.

## Almacenamiento intermedio

- **Archivos CSV**
  - Formato utilizado para almacenar la información descargada.
  - Cada ejecución genera un CSV por retailer y zona.
  - Durante el scraping, se utiliza una extensión `.tmp` para evitar procesar archivos incompletos.
  - Al finalizar correctamente la descarga, el archivo se renombra a `.csv`.

Este enfoque permite:
- Mantener un histórico de datos descargados.
- Separar claramente la fase de obtención de datos de la fase de carga en base de datos.

## Base de datos

- **MySQL**
  - Sistema de gestión de base de datos utilizado para almacenar la información final.
  - Permite realizar consultas y análisis posteriores de forma eficiente.
  - La base de datos se crea previamente por el usuario (por ejemplo, mediante Docker).

- **Carga de datos**
  - Un script específico (`csv_to_mysql_importer.py`) se encarga de:
    - Leer los CSV generados.
    - Procesar y normalizar la información.
    - Conectarse a MySQL mediante parámetros de configuración.
    - Crear la tabla `ofertas` si no existe.
    - Insertar los datos en la base de datos.

## Entorno de ejecución

- **Ejecución por línea de comandos**
  - Todos los scripts se ejecutan desde consola.
  - La configuración se realiza mediante parámetros, sin necesidad de modificar el código.
  - Esto facilita la automatización y la ejecución en distintos entornos.

## Arquitectura general

- Scripts de scraping desacoplados por retailer.
- Almacenamiento temporal en CSV.
- Procesamiento posterior y carga en base de datos.
- Diseño modular, preparado para añadir nuevos retailers o ampliar el análisis en el futuro.

# Instalación y ejecución

A continuación se detalla cómo instalar y ejecutar el proyecto, así como los recursos externos necesarios para que funcione correctamente.

---

## Recursos externos necesarios

Para poder ejecutar la solución se necesitan los siguientes elementos externos al código:

1. **Repositorio del proyecto**
   - Descargar o clonar la solución desde el repositorio.

2. **Base de datos MySQL**
   - Es necesario crear una base de datos en MySQL donde se almacenará la información.
   - Puede utilizarse, por ejemplo, una instancia de MySQL en Docker Desktop.

3. **Directorio local para CSV**
   - Crear un directorio en el equipo donde se generarán los archivos CSV.
   - Esta ruta se pasará como parámetro a los scripts.

---

## Instalación

1. **Descargar la solución**
   - Clonar o descargar el repositorio del proyecto en el equipo local.

2. **Preparar MySQL**
   - Levantar una instancia de MySQL.
   - Crear una base de datos vacía con el nombre que se usará posteriormente en el script importador.

3. **Crear carpeta para CSV**
   - Crear una carpeta en el sistema de archivos donde se guardarán los CSV.
   - Ejemplo:
     - Windows: `C:\retailers\csvs`
     - Linux/Mac: `/home/usuario/retailers/csvs`

---

## Ejecución

El flujo de ejecución del proyecto se divide en dos fases claramente diferenciadas:

1. **Obtención de información (Web Scraping)**
2. **Procesamiento e importación a MySQL**

---

## 1. Ejecución de los scripts de scraping

Los scripts de scraping disponibles son:

- `dia_scraper.py`
- `consum_scraper.py`

Cada retailer dispone de su propio script, aunque todos comparten la misma forma de ejecución.

### Parámetros

- `--cp`  
  Código Postal de la zona de la cual se quiere obtener la información.

- `--output_directory`  
  Directorio donde se crearán los archivos CSV.

### Ejemplo de ejecución

```bash
python dia_scraper.py --cp "46001" --output_directory "ruta_a_tus_csvs"
```

## Funcionamiento del scraper

El scraper es el encargado de obtener la información publicada por cada retailer online y almacenarla en archivos CSV para su posterior procesamiento.

### Pasos del proceso

- Accede a la web del retailer correspondiente.
- Establece el **código postal** indicado para obtener información zonificada.
- Recorre las **categorías y subcategorías** disponibles en la web.
- Extrae la **información de los productos**.
- Crea un archivo con extensión `.tmp` en la ruta indicada.
- Va escribiendo la información obtenida en dicho archivo `.tmp`.
- Al finalizar correctamente el proceso, renombra el archivo de `.tmp` a `.csv`.

Este mecanismo asegura que solo se procesen archivos completos.

### Ejecuciones múltiples

Este proceso puede ejecutarse múltiples veces:

- Para distintos **retailers**.
- Para distintas **zonas geográficas** (códigos postales).

---

## 2. Ejecución del script de importación a MySQL

El script encargado de importar los datos de los CSV a la base de datos es:

- `csv_to_mysql_importer.py`

### Parámetros

- `--host`: Host donde se encuentra la base de datos MySQL.
- `--port`: Puerto de conexión a MySQL.
- `--user`: Usuario de la base de datos.
- `--password`: Contraseña del usuario.
- `--database`: Nombre de la base de datos.
- `--csv_dir`: Directorio donde se encuentran los CSV a procesar.

### Ejemplo de ejecución

```bash
python csv_to_mysql_importer.py --host "localhost" --port "3306" --user "tu_usuario" --password "tu_contraseña" --database "nombre_bd" --csv_dir "ruta_a_tus_csvs"
```

## Funcionamiento del importador

- Recorre todos los archivos CSV presentes en el directorio indicado.
- Procesa y trata la información contenida en cada archivo.
- Se conecta a la base de datos MySQL con los parámetros proporcionados.
- Comprueba si existe la tabla `ofertas`:
  - Si no existe, la crea automáticamente.
- Inserta los datos en la base de datos.

---

## Gestión de archivos procesados

Una vez un CSV ha sido procesado correctamente:

- El script crea, si no existe, una carpeta llamada `_PROCESSED_FILES` dentro del directorio indicado en `--csv_dir`.
- El archivo CSV procesado se mueve a dicha carpeta `_PROCESSED_FILES`.

Esto permite:

- Evitar reprocesar archivos ya importados.
- Conservar un histórico de los ficheros descargados y procesados.

---

## Resumen del flujo completo

1. Ejecutar un scraper por retailer y zona → se generan archivos CSV.
2. Ejecutar el importador → los CSV se cargan en MySQL.
3. Los CSV procesados se mueven a `_PROCESSED_FILES` para mantener histórico.
