import pytest
import mysql.connector
from mysql.connector import Error
from task_manager import (
    vytvoreni_tabulky,
    db_pridat_ukol,
    db_aktualizovat_ukol,
    db_odstranit_ukol,
)

###  Konfigurace testovací databáze 
TEST_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1111",
    "database": "task_manager_test",
}


###  Fixture 

@pytest.fixture(scope="function")
def db_setup():
    """
    Fixture pro připojení k testovací databázi a nastavení testovacího prostředí.
    Vytvoří tabulku ukoly před testem a smaže ji po testu.
    """
    # vytvoření testovací DB pokud neexistuje
    base_cfg = {k: v for k, v in TEST_CONFIG.items() if k != "database"}
    base_conn = mysql.connector.connect(**base_cfg)
    base_conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {TEST_CONFIG['database']}")
    base_conn.commit()
    base_conn.close()

    # připojení k testovací DB
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()

    # vytvoření tabulky ukoly
    vytvoreni_tabulky(conn)

    # předání připojení a kurzoru testům
    yield conn, cursor

    # úklid po testu: smazání tabulky
    cursor.execute("DROP TABLE IF EXISTS ukoly")
    conn.commit()

    # uzavření připojení
    cursor.close()
    conn.close()


###  Testy: pridat_ukol

def test_pridat_ukol_pozitivni(db_setup):
    """Pozitivní: přidání úkolu s platným názvem a popisem uloží záznam do DB."""
    conn, cursor = db_setup

    nove_id = db_pridat_ukol(conn, "Testovací úkol", "Popis testovacího úkolu")

    # ověření vložení přes cursor
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (nove_id,))
    result = cursor.fetchone()
    assert result is not None, "Záznam nebyl vložen do tabulky."
    assert result[1] == "Testovací úkol", "Název není správný."
    assert result[2] == "Popis testovacího úkolu", "Popis není správný."
    assert result[3] == "Nezahájeno", "Výchozí stav by měl být 'Nezahájeno'."


def test_pridat_ukol_negativni(db_setup):
    """Negativní: vložení NULL jako názvu vyvolá výjimku (NOT NULL constraint)."""
    conn, cursor = db_setup

    with pytest.raises(Error):
        cursor.execute("INSERT INTO ukoly (nazev, popis) VALUES (NULL, %s)", ("Popis",))
        conn.commit()


###  Testy: aktualizovat_ukol

def test_aktualizovat_ukol_pozitivni(db_setup):
    """Pozitivní: změna stavu existujícího úkolu se projeví v DB."""
    conn, cursor = db_setup

    ukol_id = db_pridat_ukol(conn, "Úkol ke změně", "Popis")
    ovlivneno = db_aktualizovat_ukol(conn, ukol_id, "Probíhá")

    # ověření aktualizace přes cursor
    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (ukol_id,))
    result = cursor.fetchone()
    assert ovlivneno == 1, "Měl být aktualizován právě 1 řádek."
    assert result[0] == "Probíhá", "Stav nebyl správně aktualizován."


def test_aktualizovat_ukol_negativni(db_setup):
    """Negativní: aktualizace neexistujícího ID nezmění stav databáze."""
    conn, cursor = db_setup

    # počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_pred = cursor.fetchone()[0]

    ovlivneno = db_aktualizovat_ukol(conn, 999999, "Hotovo")

    # počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_po = cursor.fetchone()[0]

    assert ovlivneno == 0, "Žádný řádek by neměl být změněn."
    assert pocet_pred == pocet_po, "Aktualizace neexistujícího ID změnila stav databáze."


###  Testy: odstranit_ukol

def test_odstranit_ukol_pozitivni(db_setup):
    """Pozitivní: odstranění existujícího úkolu ho smaže z DB."""
    conn, cursor = db_setup

    ukol_id = db_pridat_ukol(conn, "Úkol k odstranění", "Popis")
    odstranenych = db_odstranit_ukol(conn, ukol_id)

    # ověření smazání přes cursor
    cursor.execute("SELECT * FROM ukoly WHERE id = %s", (ukol_id,))
    result = cursor.fetchone()
    assert odstranenych == 1, "Měl být odstraněn právě 1 řádek."
    assert result is None, "Záznam nebyl správně smazán."


def test_odstranit_ukol_negativni(db_setup):
    """Negativní: mazání neexistujícího záznamu nezmění stav databáze."""
    conn, cursor = db_setup

    # počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_pred = cursor.fetchone()[0]

    odstranenych = db_odstranit_ukol(conn, 999999)

    # počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    pocet_po = cursor.fetchone()[0]

    assert odstranenych == 0, "Žádný řádek by neměl být odstraněn."
    assert pocet_pred == pocet_po, "Mazání neexistujícího záznamu změnilo stav databáze."
