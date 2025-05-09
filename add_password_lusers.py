#Version 1.0
#Fecha 30/01/2025
#Autor: Julio de Sande. IES Santa Lucía del Trampal
#Cometido: El objetivo de este script es añadir contraseñas masivas extra a grupos de usuarios ldap del sistema,
# para facilitar la administración informática. 
#
# Ejecución:
#   1) Cambiar variable: "mi_servidor_ldap"
#   2) En un equipo con Xubuntu 22 (no ejecutar en el servidor): apt-get install python3-pip; pip3 install ldap3
#   3) Ejecutar script: python3 add_password_lusers.py
#
# Notas: 
# -Probado con Python 3.10.12 (Xubuntu 22.04)  
# -En controlies podemos ver los grupos, los miembros de ese grupo , y el identificador de dicho grupo. (Hay grupos sin miembros)

import ldap3
import os
import sys
import time
import hashlib
import base64
from typing import Literal
#import crypt
#import bcrypt

#Cambia aquí la Ip de tu servidor
#------------------------------------------
mi_servidor_ldap = 'ldap://172.23.96.2:389'
#------------------------------------------

cadena_principal_ldap = 'cn=admin,ou=people,dc=instituto,dc=extremadura,dc=es'
conn = None #Variable conexión.
Tipo_Conexion = Literal["PEOPLE", "GROUP"]


#SHA1 sin "salt": Algoritmo con colisiones, no es seguro. Pero más que suficiente para almacenar
#los datos codificados en la base de datos. Dada una misma entrada siempre produce la misma salida, esto nos
#va a permitir poder eliminar la contraseña a partir de la contraseña original, sin encriptar.
#Se han probado otros algoritmos más seguros sha1 con salt, sha515, bcrypt ... pero no funcionan.

def sha1_hash(password):
    sha = hashlib.sha1(password.encode('utf-8'))
    digest = sha.digest()
    return "{SHA}" + base64.b64encode(digest).decode('utf-8')


#No funciona
#def bcrypt_hash(password):
#    salt = bcrypt.gensalt()
#    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
#    return "{BCRYPT}" + hashed.decode('utf-8')

# CryptSha512: Versión avanzada de SHA-2. Incorpora un "salt" (cadena aleatoria) en el proceso. 
# Algoritmo seguro, dificulta la reversión del hash a la contraseña original.
# Dada una misma entrada no se produce la misma salida.
# Para borrar una encriptación generada por este algoritmo, tendremos que borrar la cadena literal {CRYPT}$6 ....
# Este si funciona, pero la librería crypt está deprecada y se va a eliminar en la próxima versión de python.
#def generate_sha512_hash(password):
#    salt = crypt.mksalt(crypt.METHOD_SHA512)
#    hashed_password = crypt.crypt(password, salt)
#    return "{CRYPT}" + hashed_password


def print_slow(str):
    for char in str:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.03)

def pintar_cabecera():

    os.system('clear')
    
    print ("""    
██╗     ██████╗  █████╗ ██████╗     ██████╗ ██╗    ██╗██████╗ 
██║     ██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██║    ██║██╔══██╗
██║     ██║  ██║███████║██████╔╝    ██████╔╝██║ █╗ ██║██║  ██║
██║     ██║  ██║██╔══██║██╔═══╝     ██╔═══╝ ██║███╗██║██║  ██║
███████╗██████╔╝██║  ██║██║         ██║     ╚███╔███╔╝██████╔╝
╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝         ╚═╝      ╚══╝╚══╝ ╚═════╝""")                                       
    print("=" * 62)
    print("CONTRASEÑAS MASIVAS USUARIOS LDAP - By J. de Sande".center(62))
    print("=" * 62)
    print("\n[!] ADVERTENCIA: REALIZAR COPIA DE SEGURIDAD LDAP [!]")
    print("    +--------------------------------------------+")                                           
    print("    |  > systemctl stop slapd                    |")
    print("    |  > slapcat -l /root/CopiaSeguridad.ldif    |")
    print("    |  > systemctl start slapd                   |")                                                    
    print("    +--------------------------------------------+")

def pintar_menu():
     
    print("\n[*] OPERACIONES DISPONIBLES:\n")
    print("    1) Añadir nueva contraseña")
    print("    2) Añadir contraseña a un grupo")
    print("    3) Eliminar contraseña insertada")
    print("    4) Mostrar usuario para comprobar inserción")
    print("    5) Abortar misión\n")


def pide_contraseña():
    
    contraseña = input("\n[?] Introduce la nueva clave: ")
    if len(contraseña) == 0:
        print_slow("\n[X] Error: Clave vacía detectada. Abortando operación.\n")
        input("[ENTER] para continuar...")
        return False

    respuesta = input("\n[?] Encriptamos la contraseña: Sha1(Recomendado)(1), Texto Plano(2): ")
    
    if respuesta == '1':
        hashed_password = sha1_hash(contraseña)
        print_slow ("\n[*] Codificando contraseña en 'Sha1': "+hashed_password+"...\n")
        contraseña = hashed_password
    elif respuesta == '2':
        print_slow ("\n[*] La contraseña se almacenará en texto plano: "+contraseña+"...\n")
    else:    
        print("Opción no válida. Por favor, intente de nuevo.")
        input("[ENTER] para continuar...")
        return False

    return contraseña


#Opción 1 del menu. Añade una contraseña.
#---------------------------------------
def añadir_contraseña():

    profesAlumnosTodos = input("\n[?] Objetivo: Profesores(1), Alumnos(2), o Todos(3): ")
    if profesAlumnosTodos != "1" and profesAlumnosTodos != "2" and profesAlumnosTodos != "3":
        print_slow("\n[X] Error: Objetivo no válido. Abortando operación.\n")
        input("[ENTER] para continuar...")
        return                                                    
    
    contraseña = pide_contraseña() 
    if not contraseña:
        return
    
    print_slow("\n[*] Iniciando inserción de contraseñas en la base de datos...\n")

    numeroInyecciones=0;
    for entry in conn.entries:
        uid=entry['uid']
        home=entry['homeDirectory'].value
        result=False
        if len (uid): 
            dn = f'uid={uid},ou=People,dc=instituto,dc=extremadura,dc=es'
            
            if (profesAlumnosTodos=="3"):   
                result = conn.modify(dn, {'userPassword': [(ldap3.MODIFY_ADD, [contraseña])]})

            elif profesAlumnosTodos=="2" and "alumnos" in home:
                result = conn.modify(dn, {'userPassword': [(ldap3.MODIFY_ADD, [contraseña])]})
        
            elif profesAlumnosTodos=="1" and "profesor" in home:
                result = conn.modify(dn, {'userPassword': [(ldap3.MODIFY_ADD, [contraseña])]})

            if (result == True):
                print (f"[*] Añadiendo contraseña: {contraseña} a el usuario: {uid}")
                numeroInyecciones=numeroInyecciones+1    
          
    print (f"[*] Total inserciones: {numeroInyecciones}")
    print_slow("\n[+] Operación completada. Cerrando conexiones...\n")
    input("[ENTER] para volver al menú principal...")
    

#Elimina una contraseña de de todos los usuarios.
#--------------------------------------------------------------------
def borrar_contraseña():
    
    contraseña = input("\n[?] Introduce la contraseña a eliminar: ")
    if len(contraseña) == 0:
        print_slow("\n[X] Error: Clave vacía detectada. Abortando operación.\n")
        input("[ENTER] para continuar...")
        return
    
    respuesta = input("\n[?] Encriptamos la contraseña (Solo para Sha1):('s/n')")
    if respuesta == 's' or respuesta == "S":
        hashed_password = sha1_hash(contraseña)
        contraseña = hashed_password 
     
    print_slow(f"\n[!] Iniciando borrado contraseña: { contraseña } en la base de datos...\n")

    numeroBorrados=0
    for entry in conn.entries:
        uid=entry['uid']
        if len (uid) > 0:# and uid=="nombreusuario:"
            dn = f'uid={uid},ou=People,dc=instituto,dc=extremadura,dc=es'
            result=conn.modify(dn, {'userPassword': [(ldap3.MODIFY_DELETE, contraseña)]})
            if result == True:
                print (f"[*] Borrando contraseña: {contraseña} a: {uid}")
                numeroBorrados=numeroBorrados+1
            else:
                print (f"[*] No se Borra contraseña: {contraseña} a: {uid}")
                
    print (f"[*] Total borrados: {numeroBorrados}")
    print_slow("\n[+] Operación completada. Cerrando conexiones...\n")
    input("[ENTER] para volver al menú principal...")

def mostrar_usuario ():
    usuario = input("\n[?] Introduce el usuario a buscar: ")
    if len(usuario) == 0:
        print_slow("\n[X] Error: Cadena vacía. Abortando operación.\n")
        input("[ENTER] para continuar...")
        return
    print ("\n")

    encontrado=False
    for entry in conn.entries:
        uid=entry['uid']
        if (uid==usuario):
            print (entry)
            encontrado=True
    
    if (encontrado):
        print_slow("\n[+] Usuario encontrado. Cerrando conexiones...\n")
    else:
        print_slow("\n[+] Usuario NO encontrado. Cerrando conexiones...\n")

    input("[ENTER] para volver al menú principal...")


def añadir_contraseña_grupo ():

    contraseña = pide_contraseña() 
    if not contraseña:
        return

    grupo = input("\n[?] Busca el ID grupo en Controlies (chequea que tiene usuarios dentro) : ")
    if len(contraseña) == 0:
        print_slow("\n[X] Error: Grupo vacío. Abortando operación.\n")
        input("[ENTER] para continuar...")
        return
 
    numeroInyecciones=0;
    
    print_slow(f"\n[*] Iniciando busqueda del grupo {grupo }...\n")
    encontrado=False

    for entry in conn.entries:
        guid= str(entry['gidNumber'])
        result=False
        if len (guid): 
            if (grupo == guid):
                encontrado="True"
                print_slow(f"\n[*] Encontrado grupo {grupo }...\n")
                miembros = str (entry['member'])
                miembros = miembros.strip("[]")
                partes = miembros.split("', '")
                partes = [parte.strip("'") for parte in partes]
                for parte in partes:
    
                    dn = parte
                    if len(dn):
                        result = conn.modify(dn, {'userPassword': [(ldap3.MODIFY_ADD, [contraseña])]})
                        if (result == True):
                            #print (f"[*] Añadiendo contraseña: {contraseña} a el usuario: {uid} con grupo: {grupo}")
                            print (f"[*] Añadiendo contraseña: {contraseña}:\n {dn}")
                            numeroInyecciones=numeroInyecciones+1    
          
    if not encontrado:
        print (f"[!] No se ha encontrado el grupo:{grupo}")  
    print (f"[*] Total inserciones: {numeroInyecciones}")
    print_slow("\n[+] Operación completada. Cerrando conexiones...\n")
    input("[ENTER] para volver al menú principal...")


def conexion_ldap (parametro:Tipo_Conexion):

    server = ldap3.Server(mi_servidor_ldap, get_info=ldap3.ALL)
    conn = ldap3.Connection(server, cadena_principal_ldap ,contra_admin_ldap, auto_bind=True)
    # Realizar una búsqueda
    if parametro=="PEOPLE":
        base_dn = 'ou=People,dc=instituto,dc=extremadura,dc=es'
        search_filter = '(objectClass=*)'
        #conn.search(base_dn, search_filter, attributes=['uid','cn','gidNumber','homeDirectory','userPassword'])
        conn.search(base_dn, search_filter, attributes=['uid','cn','homeDirectory','userPassword'])
        
    elif parametro=="GROUP":
        base_dn = 'ou=Group,dc=instituto,dc=extremadura,dc=es'
        search_filter = '(objectClass=*)'
        conn.search(base_dn, search_filter, attributes=['gidNumber','member'])
    
    return conn 


def pide_contra_ldap():
    global contra_admin_ldap
    global mi_servidor_ldap

    print (f"\n[*] Iniciando conexión con: {mi_servidor_ldap}")
    contra_admin_ldap = input("[?] Introduce la clave de tu servidor Ldap: ")
    if len(contra_admin_ldap) == 0:
        print_slow("\n[X] Error: Clave vacía detectada.\n")
        print("Saliendo del programa...\n")
        sys.exit(0)       
    try:
        conn=conexion_ldap("PEOPLE")    
    
    except ldap3.core.exceptions.LDAPException as e:
        print(f"[!] Error de conexión:{mi_servidor_ldap} {str(e)}")
        print("Saliendo del programa...\n")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error inesperado: {str(e)}")
        print("Saliendo del programa...\n")
        sys.exit(0)
    
    print_slow ("\n[*] Conexión establecida con la base de datos ... \n")
    return True

#Flujo principal
if __name__ == "__main__":

    pintar_cabecera()
    pide_contra_ldap()
    
    while True:
          
        pintar_cabecera()
        pintar_menu()
        opcion = input("[?] Seleccione una opción (1-5): ")

        try:       
           
            if opcion == "1":
                conn=conexion_ldap("PEOPLE")
                añadir_contraseña()   
            elif opcion == "2":
                conn=conexion_ldap("GROUP")
                añadir_contraseña_grupo()
            elif opcion == "3":
                conn=conexion_ldap("PEOPLE")
                borrar_contraseña()
            elif opcion == "4":
                conn=conexion_ldap("PEOPLE")
                mostrar_usuario()
            elif opcion == "5":
                print("\n[!] Saliendo del programa...\n")
                break
            else:    
                print("\n[!] Opción no válida. Por favor, intente de nuevo.\n")
                input("[ENTER] para volver al menú principal...")
        
        except ldap3.core.exceptions.LDAPException as e:
            print(f"Error de conexión LDAP: {str(e)}")
            input("[ENTER] para volver al menú principal...")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            input("[ENTER] para volver al menú principal...")
       
if conn is not None:
    conn.unbind()


