# Task Manager 2

Konzolová aplikace pro správu úkolů s ukládáním do **MySQL databáze**. Podporuje operace CRUD (Create, Read, Update, Delete) nad tabulkou úkolů.

## Požadavky

- Python 3.6 nebo novější
- MySQL server (testováno na MySQL 9.0.6)

## Instalace závislostí

```powershell
pip install -r requirements.txt
```

## Konfigurace databáze

Přihlašovací údaje se načítají ze souboru `.env`. Zkopírujte šablonu a doplňte své hodnoty:

```powershell
copy .env.example .env
```

Obsah `.env`:

```
DB_HOST=127.0.0.1
DB_USER=your_username
DB_PASSWORD=your_password
```

Databáze `task_manager` se vytvoří automaticky při prvním spuštění.

## Spuštění

```powershell
python src/task_manager.py
```

Po spuštění se zobrazí hlavní menu:

```
Správce úkolů - Hlavní menu
1. Přidat úkol
2. Zobrazit úkoly
3. Aktualizovat úkol
4. Odstranit úkol
5. Ukončit program
```

## Spuštění testů

Testy používají oddělenou databázi `task_manager_test`, která se vytvoří a po každém testu smaže automaticky.

```powershell
pytest test/
```

Chcete-li testy spustit proti produkční databázi (nedoporučeno), nastavte v `test/test_task_manager.py`:

```python
pouzivat_test_db = False
```
