# Generador de Contraseñas Masivas

El objetivo de este script es añadir contraseñas masivas extra a grupos de usuarios ldap del sistema,
para facilitar la administración informática

## Casos de uso

Puede ser útil para las siguientes situaciónes:

###1) Asistencia a un profesor en el aula.
    Si disponemos de una contraseña secreta pero fácil de recordar, la asistencia cuando el profesor da clases será más sencilla.
###2) Pruebas de diágnostico 
    Podemos generar una contraseña temporal sencilla para los alumnos. Así se agilizan el acceso a ordenadores, práctico cuando muchos alumnos están realizando una prueba.
###3)
    Se pueden generar contraseñas para grupos concretos que trabajen mucho con ordenadores, como por elemplo los alumnos de Informática.


## Puesta en marcha

###1) Editar el script, cambiando la variable: "mi_servidor_ldap"
###2) En un equipo cliente con Xubuntu 22 (no ejecutar en el servidor): 
```bash
    apt-get install python3-pip
    pip3 install ldap3
```
###3) Ejecutar script: 
```bash
    python3 add_password_lusers.py
```

## Copia de Seguridad de Ldap.

Es importante realizar una copia de seguridad de ldap antes de ejecutar el script.
El script está probado por distintos compañeros, pero la modificar el árbol ldap, se recomienda hacer una copia de seguridad.

### Generar copia de seguridad de ldap
```bash
systemctl stop slapd                   
slapcat -l /root/CopiaSeguridad.ldif    
systemctl start slapd                                                                    
```

### Restablecer copia de seguridad de ldap
```bash
slapadd -n 1 -l backup_ldap_YYYYMMDD.ldif
permisos
```
