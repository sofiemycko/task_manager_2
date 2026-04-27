import pytest
import mysql.connector
from mysql.connector import Error
from src.task_manager import (
    db_pridat_ukol,
    db_aktualizovat_ukol,
    db_odstranit_ukol,
)

###  Konfigurace testovací databáze 
pouzivat_test_db = True # Pokud True, testy budou používat databázi task_manager_test. Pokud False, použijí produkční databázi task_manager.

###  Fixture 
@pytest.fixture(scope="function")
def db_setup():
    """
    Fixture pro připojení k databázi a nastavení testovacího prostředí.
    Pokud pouzivat_test_db=True, vytvoří testovací databázi task_manager_test a tabulku ukoly.
    Po testu tabulku smaže. Při pouzivat_test_db=False použije hlavní databázi task_manager.
    """
    database = "task_manager_test" if pouzivat_test_db else "task_manager"

    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="1111",
        use_pure=True,  # V mém případě se bez toho nebylo možné k MySQL 9.0.6 připojit
    )
    cursor = conn.cursor()

    # vytvoření testovací databáze (pokud je nastaveno) a přepnutí na ni
    if pouzivat_test_db:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    cursor.execute(f"USE {database}")
    conn.commit()

    # vytvoření tabulky ukoly (pouze pro testovací DB)
    if pouzivat_test_db:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ukoly (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                nazev           VARCHAR(255)                           NOT NULL,
                popis           TEXT                                   NOT NULL,
                stav            ENUM('Nezahájeno', 'Probíhá', 'Hotovo')
                                DEFAULT 'Nezahájeno'                   NOT NULL,
                datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP     NOT NULL
            )
        """)
        conn.commit()

    # předání připojení a kurzoru testům
    yield conn, cursor

    # úklid po testu: smazání tabulky ukoly (pouze pro testovací DB)
    if pouzivat_test_db:
        cursor.execute("DROP TABLE IF EXISTS ukoly")
        conn.commit()

    # uzavření připojení
    cursor.close()
    conn.close()


###  Testy: pridat_ukol
# Pozitivní: přidání úkolu s platným názvem a popisem uloží záznam do DB.
def test_pridat_ukol_pozitivni(db_setup):
    conn, cursor = db_setup

    # testovací data
    nazev="Testovací úkol"
    popis="Popis testovacího úkolu"
    stav="Nezahájeno"

    nove_id = db_pridat_ukol(conn, nazev, popis)

    # ověření vložení přes cursor
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (nove_id,))
    result = cursor.fetchone()
    assert result is not None, "Záznam nebyl vložen do tabulky."
    assert result[1] == nazev, "Název není správný."
    assert result[2] == popis, "Popis není správný."
    assert result[3] == stav, "Výchozí stav by měl být 'Nezahájeno'."

# Negativní: vložení NULL jako popisu vyvolá výjimku (NOT NULL constraint).
def test_pridat_ukol_negativni(db_setup):
    conn, cursor = db_setup
    
    # testovací data
    nazev = None
    popis = "Popis"

    with pytest.raises(Error):
        db_pridat_ukol(conn, nazev, popis)


###  Testy: aktualizovat_ukol
# Pozitivní: změna stavu existujícího úkolu se projeví v DB.
def test_aktualizovat_ukol_pozitivni(db_setup):
    conn, cursor = db_setup
    
    # testovací data
    nazev = "Úkol ke změně"
    popis = "Popis"
    novy_stav = "Probíhá"

    ukol_id = db_pridat_ukol(conn, nazev, popis)
    ovlivneno = db_aktualizovat_ukol(conn, ukol_id, novy_stav)

    # ověření aktualizace přes cursor
    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (ukol_id,))
    result = cursor.fetchone()
    assert ovlivneno == 1, "Měl být aktualizován právě 1 řádek."
    assert result[0] == novy_stav, "Stav nebyl správně aktualizován."

# Negativní: aktualizace neexistujícího ID nezmění stav databáze.
def test_aktualizovat_ukol_negativni(db_setup):
    conn, cursor = db_setup

    # testovací data
    neexistujici_id = 999999
    novy_stav = "Hotovo"

    # počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_pred = cursor.fetchone()[0]

    ovlivneno = db_aktualizovat_ukol(conn, neexistujici_id, novy_stav)

    # počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_po = cursor.fetchone()[0]

    assert ovlivneno == 0, "Žádný řádek by neměl být změněn."
    assert pocet_pred == pocet_po, "Aktualizace neexistujícího ID změnila stav databáze."


###  Testy: odstranit_ukol
# Pozitivní: odstranění existujícího úkolu ho smaže z DB.
def test_odstranit_ukol_pozitivni(db_setup):
    conn, cursor = db_setup
    
    # testovací data
    nazev = "Úkol k odstranění"
    popis = "Popis"

    ukol_id = db_pridat_ukol(conn, nazev, popis)
    odstranenych = db_odstranit_ukol(conn, ukol_id)

    # ověření smazání přes cursor
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (ukol_id,))
    result = cursor.fetchone()
    assert odstranenych == 1, "Měl být odstraněn právě 1 řádek."
    assert result is None, "Záznam nebyl správně smazán."

# Negativní: mazání neexistujícího záznamu nezmění stav databáze.
def test_odstranit_ukol_negativni(db_setup):
    conn, cursor = db_setup
    
    # testovací data
    neexistujici_id = 999999

    # počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_pred = cursor.fetchone()[0]

    odstranenych = db_odstranit_ukol(conn, neexistujici_id)

    # počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_po = cursor.fetchone()[0]

    assert odstranenych == 0, "Žádný řádek by neměl být odstraněn."
    assert pocet_pred == pocet_po, "Mazání neexistujícího záznamu změnilo stav databáze."