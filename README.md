# Tema 5: Transações, Concorrência e Migrações no Peewee ORM

Este guia foi elaborado para a apresentação e compartilhamento com a turma sobre o **Tema 5: Transações, Concorrência e Migrações de Banco de Dados** usando a biblioteca **Peewee** em Python.

## Sumário

1. [Introdução ao Tema](#1-introdução-ao-tema)

2. [Gerenciamento de Transações (`db.atomic()`, `transaction()`, `savepoint()`)](#2-gerenciamento-de-transações)

3. [Savepoints e Transações Aninhadas](#3-savepoints-e-transações-aninhadas)

4. [Tratamento de Concorrência e Rollback](#4-tratamento-de-concorrência-e-rollback)

5. [Migrações de Esquema com `playhouse.migrate`](#5-migrações-de-esquema-com-playhousemigrate)

6. [Prática Exigida: Código Completo Demonstrativo](#6-prática-exigida-código-completo-demonstrativo)

7. [Conclusão e Boas Práticas](#7-conclusão-e-boas-práticas)

## 1. Introdução ao Tema

Em aplicações Orientadas a Objetos (OO), garantir a **integridade dos dados** no banco relacional é um desafio crítico. Quando executamos operações complexas ou simultâneas, precisamos de garantias de segurança (propriedades ACID):

* **Atomicidade:** Ou todas as operações de uma tarefa terminam com sucesso, ou NENHUMA é aplicada.

* **Consistência e Isolamento:** Prevenir que falhas de rede ou concorrência deixem os dados em um estado quebrado.

* **Evolução de Esquema:** Alterar tabelas existentes (adicionar/remover colunas) sem perder os registros cadastrados em produção.

O ORM Peewee oferece ferramentas simples e poderosas para gerenciar transações e migrações.

## 2. Gerenciamento de Transações

### `db.atomic()`

A forma padrão e recomendada de gerenciar transações no Peewee é com o gerenciador de contexto `db.atomic()`.

* Se o bloco `with` terminar sem erros, o Peewee executa um **`COMMIT`** automático.

* Se ocorrer uma exceção dentro do bloco `with`, o Peewee executa um **`ROLLBACK`** automático.

```
from peewee import SqliteDatabase, Model, CharField, DecimalField

db = SqliteDatabase('banco.db')

class Conta(Model):
    titular = CharField()
    saldo = DecimalField(decimal_places=2)

    class Meta:
        database = db

# Transação atômica básica
with db.atomic():
    Conta.create(titular='Alice', saldo=1000.00)
    Conta.create(titular='Bob', saldo=500.00)

```

## 3. Savepoints e Transações Aninhadas

Um **Savepoint** é um ponto de restauração intermediário dentro de uma transação. Ele permite reverter (rollback) apenas uma sub-operação específica sem cancelar toda a transação externa.

No Peewee, o Savepoint é gerenciado de forma transparente e idiomática: quando um bloco `db.atomic()` é aninhado dentro de outro `db.atomic()`, o Peewee cria automaticamente um Savepoint.

```
with db.atomic() as transacao_principal:
    # Operação Principal
    Conta.create(titular='Carlos', saldo=500.00)

    try:
        # Bloco aninhado: Peewee cria um Savepoint automaticamente
        with db.atomic() as savepoint_secundario:
            Conta.create(titular='Operação Riscada', saldo=-100.00)
            raise ValueError("Erro simulado na sub-operação!")
    except ValueError:
        print("Sub-operação falhou! Rollback feito até o Savepoint.")

    # A criação do 'Carlos' continua preservada e será comitada!
```

## 4. Tratamento de Concorrência e Rollback

Operações financeiras (como transferências entre contas) exigem segurança absoluta: debitar de uma conta e creditar em outra deve acontecer de forma indivisível. Se ocorrer uma falha durante o processo, o estado inicial das duas contas deve ser restaurado.

### Lógica de Transferência Segura:

```
def transferir(id_origem, id_destino, valor):
    try:
        with db.atomic():
            c_origem = Conta.get_by_id(id_origem)
            c_destino = Conta.get_by_id(id_destino)

            if c_origem.saldo < valor:
                raise ValueError("Saldo insuficiente!")

            # 1. Debita da conta de origem
            c_origem.saldo -= valor
            c_origem.save()

            # Se ocorrer qualquer erro aqui, o débito acima será anulado (Rollback)

            # 2. Credita na conta de destino
            c_destino.saldo += valor
            c_destino.save()

            print("Transferência realizada com sucesso!")
    except Exception as e:
        print(f"Erro na operação: {e}. O Rollback automático protegeu os dados.")

```

## 5. Migrações de Esquema com `playhouse.migrate`

Ao longo do tempo, o sistema evolui e novos campos precisam ser adicionados às tabelas. Como não podemos apagar o banco em produção (o que destruiria os dados existentes), usamos o módulo **`playhouse.migrate`** para alterar a estrutura da tabela.

### Operações comuns:

* `add_column`: Adiciona uma nova coluna.

* `drop_column`: Remove uma coluna.

* `rename_column`: Renomeia uma coluna existente.

```
from playhouse.migrate import SqliteMigrator, migrate

migrator = SqliteMigrator(db)
status_field = CharField(default='Ativa', null=False)

# Executa o ALTER TABLE sem apagar os registros da tabela
migrate(
    migrator.add_column('conta', 'status', status_field)
)

```

## 6. Prática Exigida: Código Completo Demonstrativo

Abaixo está o script completo que atende à prática exigida pelo trabalho:

1. Simula uma transferência bancária com falha para demonstrar **rollback**.

2. Demonstra o uso de **Savepoint** em blocos aninhados para reverter sub-operações sem abortar a transação principal.

3. Executa uma **migração de banco de dados** adicionando novas colunas sem perda de dados.

```
import os
from peewee import SqliteDatabase, Model, CharField, DecimalField, IntegerField
from playhouse.migrate import SqliteMigrator, migrate

# 1. Configuração Inicial do Banco de Dados
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

# 2. Inserção de Dados Iniciais
ContaBancaria.create(titular="Alice", saldo=1000.00)
ContaBancaria.create(titular="Bob", saldo=300.00)

def exibir_saldos(titulo):
    print(f"\n--- {titulo} ---")
    for conta in ContaBancaria.select():
        print(f"ID {conta.id} | Titular: {conta.titular} | Saldo: R$ {conta.saldo:.2f}")

exibir_saldos("Saldos Iniciais")

# 3. Função de Transferência com Simulação de Falha (Rollback Total)
def transferir_valores(id_origem, id_destino, valor, simular_erro=False):
    print(f"\n>> Tentando transferir R$ {valor:.2f} da Conta {id_origem} para Conta {id_destino}...")
    try:
        with db.atomic():
            c_origem = ContaBancaria.get_by_id(id_origem)
            c_destino = ContaBancaria.get_by_id(id_destino)

            if c_origem.saldo < valor:
                raise ValueError("Saldo insuficiente!")

            # Etapa 1: Debita da origem
            c_origem.saldo -= valor
            c_origem.save()

            # Simulação de erro de sistema/rede
            if simular_erro:
                raise RuntimeError("FALHA DE CONEXÃO/SISTEMA NO MEIO DA TRANSAÇÃO")

            # Etapa 2: Credita no destino
            c_destino.saldo += valor
            c_destino.save()

            print("Transferência concluída com SUCESSO!")

    except Exception as e:
        print(f"ERRO NA OPERAÇÃO: {e}")
        print("ROLLBACK EXECUTADO! O saldo da conta de origem foi restaurado.")

# Teste 1: Transferência com Sucesso
transferir_valores(id_origem=1, id_destino=2, valor=200.00, simular_erro=False)
exibir_saldos("Saldos Após Transferência Com Sucesso")

# Teste 2: Transferência Com Erro (Demonstração de Rollback)
transferir_valores(id_origem=1, id_destino=2, valor=500.00, simular_erro=True)
exibir_saldos("Saldos Após Erro na Transferência (Valores Intactos)")

# 4. Demonstração Prática de Savepoint (Transação Aninhada)
print("\n" + "="*50)
print("DEMONSTRAÇÃO DE SAVEPOINT (db.atomic() Aninhado)")
print("="*50)

try:
    with db.atomic() as transacao_pai:
        # Cria uma conta válida na transação principal
        ContaBancaria.create(titular="Charlie", saldo=1500.00)
        print("Charlie criado na transação principal.")

        try:
            # Savepoint automático criado pelo bloco aninhado
            with db.atomic() as savepoint_filho:
                ContaBancaria.create(titular="Conta Com Erro", saldo=0.00)
                print(">> Tentando executar sub-operação com erro...")
                raise ValueError("Erro proposital na sub-operação")
        except ValueError as sub_erro:
            print(f"Erro capturado no Savepoint: {sub_erro}")
            print("Sub-operação revertida para o Savepoint. A transação principal continua!")

        # Outra operação válida na transação principal
        ContaBancaria.create(titular="David", saldo=800.00)
        print("David criado na transação principal.")

except Exception as e:
    print(f"Erro geral: {e}")

exibir_saldos("Saldos Após Demonstração de Savepoints (Charlie e David salvos, Conta Com Erro descartada)")

# 5. Demonstração de Migração de Banco de Dados
print("\n" + "="*50)
print("INICIANDO MIGRAÇÃO DE ESQUEMA (playhouse.migrate)")
print("="*50)

migrator = SqliteMigrator(db)

# Novos campos para a tabela existente
status_field = CharField(default='Ativa', null=False)
limite_field = IntegerField(default=1000)

# Execução da alteração da tabela
migrate(
    migrator.add_column('contabancaria', 'status', status_field),
    migrator.add_column('contabancaria', 'limite_credito', limite_field)
)

print("Novas colunas adicionadas com sucesso sem apagar os dados antigos")

# Verificação dos dados após a migração
cursor = db.execute_sql("SELECT id, titular, saldo, status, limite_credito FROM contabancaria;")
print("\n--- Tabela Final Pós-Migração ---")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Titular: {row[1]} | Saldo: R${row[2]:.2f} | Status: {row[3]} | Limite: R${row[4]}")

db.close()

```

## 7. Conclusão e Boas Práticas

1. **Uso do `db.atomic()`:** Sempre envolva operações de escrita críticas dentro de um bloco atômico.

2. **Uso Estratégico de Savepoints:** Utilize `db.atomic()` aninhado quando precisar isolar sub-etapas de um processo complexo.

3. **Prevenção de Locks:** Mantenha os blocos transacionais o mais curtos possível para evitar travar o banco para outros usuários.

4. **Migrações Seguras:** Sempre faça backup antes de rodar comandos do `playhouse.migrate` em bases reais.