import os
from peewee import SqliteDatabase, Model, CharField, DecimalField, IntegerField
from playhouse.migrate import SqliteMigrator, migrate

DB_NAME = 'sistema_bancario.db'

if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

db = SqliteDatabase(DB_NAME)

class ContaBancaria(Model):
    titular = CharField()
    saldo = DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        database = db

db.connect()
db.create_tables([ContaBancaria])

ContaBancaria.create(titular="Alice", saldo=1000.00)
ContaBancaria.create(titular="Bob", saldo=300.00)

def exibir_saldos(titulo):
    print(f"\n--- {titulo} ---")
    for conta in ContaBancaria.select():
        print(f"ID {conta.id} | Titular: {conta.titular} | Saldo: R$ {conta.saldo:.2f}")

exibir_saldos("Saldos Iniciais")

def transferir_valores(id_origem, id_destino, valor, simular_erro=False):
    print(f"\n>> Tentando transferir R$ {valor:.2f} da Conta {id_origem} para Conta {id_destino}...")
    try:
        with db.atomic():
            c_origem = ContaBancaria.get_by_id(id_origem)
            c_destino = ContaBancaria.get_by_id(id_destino)

            if c_origem.saldo < valor:
                raise ValueError("Saldo insuficiente!")

            c_origem.saldo -= valor
            c_origem.save()

            if simular_erro:
                raise RuntimeError("FALHA DE CONEXÃO NO MEIO DA TRANSAÇÃO!")

            c_destino.saldo += valor
            c_destino.save()

            print("Transferência concluída com SUCESSO!")

    except Exception as e:
        print(f"ERRO NA OPERAÇÃO: {e}")
        print("ROLLBACK EXECUTADO AUTOMATICAMENTE! O estado do banco permaneceu intacto.")

transferir_valores(id_origem=1, id_destino=2, valor=200.00, simular_erro=False)
exibir_saldos("Saldos Após Transferência Bem-Sucedida")

transferir_valores(id_origem=1, id_destino=2, valor=500.00, simular_erro=True)
exibir_saldos("Saldos Após Erro na Transferência (Deve ser igual ao anterior)")


print("\n" + "="*50)
print("INICIANDO MIGRAÇÃO DE ESQUEMA (playhouse.migrate)")
print("="*50)

migrator = SqliteMigrator(db)

status_field = CharField(default='Ativa', null=False)
limite_field = IntegerField(default=1000)

migrate(
    migrator.add_column('contabancaria', 'status', status_field),
    migrator.add_column('contabancaria', 'limite_credito', limite_field)
)

print("Colunas 'status' e 'limite_credito' adicionadas com sucesso!")

cursor = db.execute_sql("SELECT id, titular, saldo, status, limite_credito FROM contabancaria;")
print("\n--- Dados da Tabela Após Migração ---")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Titular: {row[1]} | Saldo: R${row[2]:.2f} | Status: {row[3]} | Limite: R${row[4]}")

db.close()