# Guía paso a paso: proyecto completo en la nube (AWS EC2 + RDS)

Nada de XAMPP ni base de datos local: el sitio y la base de datos corren
los dos en AWS, accesibles desde cualquier parte con una URL/IP pública.

Esta guía es para que tú misma (o con tu compañero) ejecutes estos pasos.
No puedo ejecutarlos por ti porque necesitan tu cuenta de AWS y tus
credenciales — eso nunca debe compartirse ni escribirse en un chat. Yo te
doy los comandos exactos y te ayudo a resolver cualquier error que te
salga, con el mensaje de error tal cual.

**Arquitectura que vamos a armar** (la misma que ya está descrita en
`ARQUITECTURA.md`, sección "Vista física"):

```
Tu navegador  -->  EC2 (Django + Gunicorn/runserver)  -->  RDS (MySQL)
```

Dos piezas separadas: **RDS** es la base de datos administrada por AWS (no
tienes que instalar ni configurar MySQL a mano), y **EC2** es el servidor
donde corre el proyecto Django. Es la forma "profesional" de hacerlo, y
también calza mejor con lo que pide la Evaluación 2 (separar la capa de
datos de la capa de aplicación).

---

## Paso 1 — Crear la cuenta de AWS (si no la tienes)

Entra a [aws.amazon.com](https://aws.amazon.com) y crea una cuenta con
capa gratuita ("Free Tier"). **Esto lo haces tú**: nombre, correo, tarjeta
(AWS la pide aunque no te cobre dentro del Free Tier). Nunca me pases esos
datos ni los escribas en el chat.

## Paso 2 — Crear la base de datos en RDS

1. En la consola de AWS, busca **RDS** → **"Create database"**.
2. Elige:
   - Engine: **MySQL**
   - Templates: **Free tier**
   - DB instance identifier: `sgr-db`
   - Master username: `sgr_admin`
   - Master password: elige una clave segura y **guárdala tú** (no me la
     cuentes). AWS la vuelve a pedir una sola vez al crear la instancia.
   - DB instance class: la que venga marcada por defecto para Free Tier
     (`db.t3.micro` o `db.t4g.micro`)
   - Storage: el valor por defecto está bien (20 GiB)
   - **Public access**: elige **Yes** (así tu instancia EC2 y tú misma
     pueden conectarse).
3. En "Additional configuration", pon **Initial database name**:
   `sgr_evaluacion`.
4. Click en **"Create database"**. Tarda unos minutos en quedar lista
   (estado "Available").
5. Cuando esté lista, entra a la instancia y copia el **"Endpoint"** (algo
   como `sgr-db.xxxxxxxxx.us-east-1.rds.amazonaws.com`) — lo vas a
   necesitar en el Paso 5.

## Paso 3 — Crear la instancia EC2 (el servidor del sitio)

1. En la consola de AWS, busca **EC2** → **"Launch instance"**.
2. Configuración:
   - Nombre: `sgr-la-serena`
   - AMI: **Amazon Linux 2023** (Free Tier eligible) — no Ubuntu
   - Tipo de instancia: `t2.micro` (Free Tier eligible)
   - Par de claves (key pair): crea uno nuevo, descárgalo (`.pem`) y
     guárdalo en un lugar seguro — no se puede volver a descargar.
   - Configuración de red (Security Group): permite **SSH (puerto 22)**
     desde "My IP", y agrega una regla para el **puerto 8000** abierto a
     "Anywhere" (0.0.0.0/0) — así se puede ver el sitio desde cualquier
     navegador.
3. Click en **"Launch instance"**.

## Paso 4 — Permitir que EC2 se conecte a RDS

1. Ve a **RDS** → tu base de datos `sgr-db` → pestaña **"Connectivity &
   security"** → click en el **VPC security group**.
2. En ese security group, agrega una regla de entrada ("Inbound rules"):
   - Tipo: **MySQL/Aurora** (puerto 3306)
   - Origen: el **security group de tu instancia EC2** (más seguro que
     "Anywhere" — escribe el nombre y AWS te lo sugiere), o si te complica
     elegirlo así, puedes usar "My IP" temporalmente mientras pruebas.
3. Guarda los cambios.

## Paso 5 — Conectarte a la instancia EC2 e instalar lo necesario

Esto se hace con **Git Bash** (el mismo que usaron en el ramo de Sistema
Operativo), no desde la consola web de AWS:

1. Abre **Git Bash** en tu computador, en la carpeta donde descargaste el
   archivo `.pem` del Paso 3.
2. Dale permisos restringidos al archivo (obligatorio, o SSH lo rechaza):
   ```bash
   chmod 400 nombre-de-tu-llave.pem
   ```
3. Conéctate por SSH a la instancia (reemplaza por el nombre real de tu
   `.pem` y la IP pública de tu instancia, que ves en la consola de EC2,
   columna "Public IPv4 address"):
   ```bash
   ssh -i nombre-de-tu-llave.pem ec2-user@IP_PUBLICA_DE_TU_INSTANCIA
   ```
   (Con Amazon Linux el usuario es **`ec2-user`**, no `ubuntu` — es lo
   que usaron en Sistema Operativo.)
   La primera vez te va a preguntar algo como "Are you sure you want to
   continue connecting (yes/no)?" — escribe `yes` y Enter.
4. Si quedaste conectado, el prompt de Git Bash cambia a algo como
   `[ec2-user@ip-xxx-xxx-xxx-xxx ~]$` — ya estás dentro de la instancia.

Desde ahí, instala lo necesario (los mismos comandos de siempre, pero
ahora corriendo dentro de la instancia, no en tu computador). Amazon
Linux usa `yum`, no `apt` (eso es de Ubuntu/Debian):

```bash
sudo yum update -y
sudo yum install -y python3-pip git
```
(Amazon Linux 2023 ya trae `python3` instalado con el módulo `venv`
incluido, así que no hace falta un paquete aparte para eso.)

> Si te sale `Permission denied (publickey)`, revisa: que el `.pem` sea
> el mismo que generaste para ESA instancia, que el `chmod 400` se haya
> aplicado bien, y que estés usando el usuario `ec2-user` (no `ubuntu`,
> no `root`, ni tu usuario de Windows).

(Nota que esta vez **no** instalamos `mysql-server` — la base de datos ya
existe en RDS, no hace falta tenerla también en la instancia.)

## Paso 6 — Subir el proyecto a la instancia

Lo más simple es tenerlo en GitHub y clonarlo:

```bash
git clone URL_DE_TU_REPOSITORIO
cd sgr_evaluacion   # o el nombre real de la carpeta clonada
```

> Si el proyecto todavía no está en GitHub, avísame y te ayudo con ese
> paso antes de seguir — lo necesitas para poder clonarlo aquí.

## Paso 7 — Configurar el proyecto para conectarse a RDS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Dentro de `.env`, deja:
```
DB_ENGINE=mysql
DB_NAME=sgr_evaluacion
DB_USER=sgr_admin
DB_PASSWORD=la_clave_que_pusiste_en_el_paso_2
DB_HOST=sgr-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=3306
DEBUG=False
ALLOWED_HOSTS=IP_PUBLICA_DE_TU_INSTANCIA_EC2
```
(`DB_HOST` es el "Endpoint" que copiaste en el Paso 2. `ALLOWED_HOSTS` es
la IP pública de la instancia EC2, que ves en la consola de EC2, columna
"Public IPv4 address". Guarda con `Ctrl+O`, Enter, y sal con `Ctrl+X`.)

## Paso 8 — Aplicar migraciones, cargar datos y levantar el sitio

```bash
python manage.py migrate
python manage.py cargar_datos_iniciales
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
```

## Paso 9 — Verificar

Abre en tu navegador: `http://IP_PUBLICA_DE_TU_INSTANCIA:8000/`

Si ves el sitio con las delegaciones y actividades cargadas, ya está todo
corriendo en la nube: la base de datos en RDS y el sitio en EC2.

## Paso 10 — Dejarlo corriendo sin tener la terminal abierta

`runserver` se corta si cierras la terminal SSH. Para que el sitio siga
funcionando aunque cierres la conexión:

```bash
nohup python manage.py runserver 0.0.0.0:8000 &
```

(Para algo más robusto, no obligatorio para la evaluación, se puede
reemplazar por Gunicorn + Nginx más adelante — se puede ver si lo
necesitas.)

---

## Paso 11 — Actualizar a una versión nueva (por ejemplo, de 1.x a 2.0)

En la instancia en uso (EC2 con MariaDB y el servicio `sgr`), se sube el zip de la versión y se ejecuta:

```bash
unzip -o sgr_evaluacion_fusionado_v2.0.zip
cd sgr_evaluacion_fusionado && source venv/bin/activate
python manage.py migrate                       # tablas y campos nuevos de la versión
python manage.py configurar_roles              # permisos nuevos por rol
python manage.py cargar_datos_iniciales        # (opcional) datos de ejemplo nuevos
python manage.py collectstatic --noinput       # estilos nuevos
sudo systemctl restart sgr
python manage.py test                          # en la 2.0 deben pasar 156 pruebas
```

El número de versión aparece en el pie de la página (por ejemplo, `v2.0.0`). Así se comprueba que el servidor quedó actualizado.

## Errores comunes

| Error | Causa probable | Solución |
|---|---|---|
| `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server...")` | El security group de RDS no deja pasar a EC2 | Revisa el Paso 4: la regla de entrada en RDS debe permitir el security group de tu instancia EC2 |
| `Access denied for user 'sgr_admin'@...` | Clave o usuario mal escritos en `.env` | Revisa `DB_USER`/`DB_PASSWORD` contra lo que pusiste al crear la base en RDS |
| El sitio no carga desde el navegador (IP pública) | Falta la regla del puerto 8000 en el security group de EC2 | Revisa el Paso 3: agrega la regla de entrada para el puerto 8000 |
| `DisallowedHost` al abrir el sitio | `ALLOWED_HOSTS` en `.env` no tiene la IP pública correcta | Corrige `ALLOWED_HOSTS` en el `.env` de la instancia y reinicia `runserver` |

---

## Resumen de lo que hago yo y lo que te corresponde a ti

| Tarea | Quién la hace |
|---|---|
| Crear cuenta AWS, poner tarjeta, manejar credenciales/claves | Tú (por seguridad, nunca yo) |
| Crear la base de datos en RDS y la instancia EC2, configurar seguridad | Tú, siguiendo los Pasos 1 a 4 |
| Conectarte por SSH y correr los comandos | Tú (te doy el comando exacto cada vez) |
| Código del proyecto ya preparado para MySQL/RDS | Ya está hecho en el proyecto que te mandé |
| Revisar un error específico que te salga | Yo, si me copias el mensaje de error exacto, tal cual |
| Subir el proyecto a GitHub (si no está) | Te ayudo si me lo pides |
