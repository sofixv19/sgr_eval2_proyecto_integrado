"""
Registra PyMySQL como reemplazo de mysqlclient.

Esto permite usar el backend 'django.db.backends.mysql' de Django con el
driver puro-Python pymysql (más fácil de instalar en Windows y en la
instancia EC2 que compilar mysqlclient). Si el proyecto está configurado
para usar SQLite (DB_ENGINE=sqlite en el .env), estas líneas no tienen
ningún efecto negativo: simplemente no se usan.
"""
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # En un entorno que solo use SQLite, pymysql puede no estar instalado.
    pass
