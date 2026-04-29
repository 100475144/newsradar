# ADR — Development Environment

## Contexto 

Para desarrollar un sistema como NEWSRADAR, un proyecto en el cual se va a trabajar de forma coordinada entre varias personas, hace falta que los desarrolladores dispongan de un entorno de desarrollo al que todos tengan acceso y que funcione de igual forma para todo el mundo. 

Otra necesidad para nuestro entorno de desarrollo es que sea altamente automatizable para que cada integrante del grupo de desarrolladores se pueda enfocar en programar su parte del código sin tener que estar instalando las dependencias del proyecto en sus equipos, las cuales irán creciendo a lo largo del proyecto, o realizar cambios manuales desde la consola continuamente para que las cosas funcionen.

## Decisión

Como no se dispone de infraestructura física para montar un entorno de desarrollo que se comparta entre el equipo de trabajo, la siguiente mejor opción es instalar un entorno de desarrollo sobre contenedores Docker, instalación que cada miembro del equipo que trabaje con el proyecto tendrá que realizar localmente en su ordenador. 

De igual forma, se prevee utilizar un sistema similar al que se propone a continuación para en un futuro despelgar el sistema en producción, facilitando de esta forma el futuro despliegue del sistema.

## Justificación

Docker es capaz de aislar la ejecución de un programa (por ejemplo, un código Python) del sistema operativo sobre el que se está ejecutando (por ejemplo, Ubuntu Linux de un PC personal) gracias a que permite crear contenedores. 

Un contenedor en Linux es un conjunto de uno o varios procesos aislados del resto del sistema operativo, para un entorno de desarrollo esto es ideal ya que se puede tener control absoluto de la configuración del sistema operativo junto con los paquetes y librerías que se instalan en este entorno y de esta forma forzar el mismo setup para todos los desarrolladores independientemente del sistema operativo en el que se ejecuten. 

De esta forma, el código que se desarrolla funcionará de igual forma en los distintos ordenadores que utilizan los desarrolladores. 

Por otro lado, utilizar contenedores Docker junto con Docker Compose permite automatizar la instalación, inicialización y  configuración del entorno de desarrollo mediante un archivo en formato **yaml** y varios archivos **Dockerfile** con los que se puede personalizar un contenedor Docker a partir de una imagen base, gracias a que permite ejecutar una serie de comandos, en nuestro caso estos archivos se utilizan para crear un setup inicial donde se instalan las dependencias necesarias del código y se inicia el código de desarrollo.

## Resultado de la decisión

Aplicando las herramientas descritas para implementar el entorno de desarrollo se llega a una solución satisfactoria en la cual la versión de desarrollo del sistema inicia correctamente tras ejecutar los siguientes comandos: 

```
docker compose build
docker compose up
```
