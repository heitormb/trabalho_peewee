# Tema 5: Transações, Concorrência e Migrações no Peewee ORM

Este guia foi elaborado pela **Equipe Gama** para a disciplina, apresentando os conceitos e a utilização prática de **Transações**, **Controle de Concorrência** e **Migrações de Esquema** utilizando o ORM Peewee em Python.

---

## Sumário
1. [Introdução ao Tema](#1-introdução-ao-tema)
2. [Gerenciamento de Transações (`db.atomic()`)](#2-gerenciamento-de-transações-dbatomic)
3. [Tratamento de Concorrência e Rollback](#3-tratamento-de-concorrência-e-rollback)
4. [Savepoints](#4-savepoints)
5. [Migrações de Banco de Dados (`playhouse.migrate`)](#5-migrações-de-banco-de-dados-playhousemigrate)
6. [Prática Exigida: Código Completo Demonstrativo](#6-prática-exigida-código-completo-demonstrativo)
7. [Conclusão e Boas Práticas](#7-conclusão-e-boas-práticas)

---

## 1. Introdução ao Tema

Em sistemas orientados a objetos modernos, a camada de persistência deve garantir a **integridade dos dados** mesmo diante de falhas de hardware, erros de código ou execuções simultâneas.

O Peewee oferece recursos robustos para responder a duas grandes necessidades:
- **Propriedades ACID (especialmente Atomicidade e Isolamento):** Garantir que operações compostas terminem 100% com sucesso ou sejam completamente anuladas (*rollback*).
- **Evolução de Esquema:** Permitir alterar tabelas e colunas em bancos já em produção sem perda de dados existentes.

---

## 2. Gerenciamento de Transações (`db.atomic()`)

Uma transação é um bloco de operações que devem ser executadas como uma unidade única e indivisível. 

No Peewee, a forma principal e idomática de gerenciar transações é através do context manager **`db.atomic()`**.

### Vantagens do `db.atomic()`:
- **Aninhamento automático:** Caso um bloco `atomic()` seja chamado dentro de outro `atomic()`, o Peewee gerencia a transação utilizando *Savepoints* de forma transparente.
- **Commit / Rollback automáticos:** Se o bloco for executado sem exceções, o `commit` ocorre ao final. Se uma exceção não tratada for lançada, ocorre o `rollback` automático.

```python
from peewee import SqliteDatabase, Model, CharField, DecimalField

db = SqliteDatabase('banco.db')

class Conta(Model):
    titular = CharField()
    saldo = DecimalField(decimal_places=2)

    class Meta:
        database = db

with db.atomic():
    Conta.create(titular='Alice', saldo=1000.00)
    Conta.create(titular='Bob', saldo=500.00)