import mysql.connector
from mysql.connector import Error

###  Konfigurace připojení k databázi 
DB_CONFIG = {
    "host": "192.168.1.235",
    "user": "root",
    "password": "1111",
    "database": "task_manager",
}


def pripojeni_db(config=None):
    """Vytvoří připojení k MySQL databázi. Vrátí objekt conn nebo None."""
    if config is None:
        config = DB_CONFIG
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        print(f"Chyba při připojení k databázi: {e}")
        return None


def vytvoreni_tabulky(conn):
    """Vytvoří tabulku ukoly, pokud ještě neexistuje."""
    sql = """
        CREATE TABLE IF NOT EXISTS ukoly (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            nazev         VARCHAR(255)                          NOT NULL,
            popis         TEXT                                  NOT NULL,
            stav          ENUM('Nezahájeno', 'Probíhá', 'Hotovo')
                          DEFAULT 'Nezahájeno'                  NOT NULL,
            datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP  NOT NULL
        )
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
    except Error as e:
        print(f"Chyba při vytváření tabulky: {e}")


###  Databázové operace (testovatelné) 

def db_pridat_ukol(conn, nazev, popis):
    """Vloží nový úkol do DB. Vrátí ID nového záznamu."""
    sql = "INSERT INTO ukoly (nazev, popis) VALUES (%s, %s)"
    cursor = conn.cursor()
    cursor.execute(sql, (nazev, popis))
    conn.commit()
    return cursor.lastrowid


def db_zobrazit_ukoly(conn):
    """Vrátí seznam úkolů se stavem Nezahájeno nebo Probíhá."""
    sql = "SELECT id, nazev, popis, stav FROM ukoly WHERE stav IN ('Nezahájeno', 'Probíhá') ORDER BY id"
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchall()


def db_aktualizovat_ukol(conn, ukol_id, novy_stav):
    """Aktualizuje stav úkolu podle ID. Vrátí počet ovlivněných řádků."""
    sql = "UPDATE ukoly SET stav = %s WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(sql, (novy_stav, ukol_id))
    conn.commit()
    return cursor.rowcount


def db_odstranit_ukol(conn, ukol_id):
    """Odstraní úkol podle ID. Vrátí počet odstraněných řádků."""
    sql = "DELETE FROM ukoly WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(sql, (ukol_id,))
    conn.commit()
    return cursor.rowcount


def db_najit_ukol(conn, ukol_id):
    """Vrátí řádek úkolu podle ID nebo None."""
    sql = "SELECT id, nazev, popis, stav FROM ukoly WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(sql, (ukol_id,))
    return cursor.fetchone()


###  UI funkce

def pridat_ukol(conn):
    """UI pro přidání úkolu - vyžádá název a popis, uloží do DB."""
    # opakuj dokud uživatel nezadá neprázdný název
    while True:
        nazev = input("\nZadejte název úkolu: ").strip()
        if not nazev:
            print("Název úkolu nesmí být prázdný. Zkuste to znovu.")
            continue
        break

    # opakuj dokud uživatel nezadá neprázdný popis
    while True:
        popis = input("Zadejte popis úkolu: ").strip()
        if not popis:
            print("Popis úkolu nesmí být prázdný. Zkuste to znovu.")
            continue
        break

    nove_id = db_pridat_ukol(conn, nazev, popis)
    print(f"Úkol '{nazev}' byl přidán (ID: {nove_id}, stav: Nezahájeno).")


def zobrazit_ukoly(conn):
    """UI pro zobrazení úkolů se stavem Nezahájeno nebo Probíhá."""
    ukoly = db_zobrazit_ukoly(conn)
    if not ukoly:  # žádné aktivní úkoly
        print("\nSeznam úkolů je prázdný.")
    else:
        print("\nSeznam úkolů (Nezahájeno / Probíhá):")
        for ukol in ukoly:
            print(f"  ID: {ukol[0]} | {ukol[1]} | {ukol[2]} | {ukol[3]}")
    print()


def aktualizovat_ukol(conn):
    """UI pro změnu stavu úkolu."""
    zobrazit_ukoly(conn)

    # výběr ID úkolu
    while True:
        vstup = input("Zadejte ID úkolu pro aktualizaci: ").strip()
        try:
            ukol_id = int(vstup)
        except ValueError:
            print("Neplatný vstup. Zadejte celé číslo.")
            continue

        if db_najit_ukol(conn, ukol_id):  # úkol existuje
            break
        else:
            print(f"Úkol s ID {ukol_id} neexistuje. Zkuste to znovu.")

    # výběr nového stavu
    print("Vyberte nový stav:")
    print("1. Probíhá")
    print("2. Hotovo")
    while True:
        volba = input("Vaše volba (1-2): ").strip()
        if volba == "1":
            novy_stav = "Probíhá"
            break
        elif volba == "2":
            novy_stav = "Hotovo"
            break
        else:
            print("Neplatná volba. Zadejte 1 nebo 2.")

    db_aktualizovat_ukol(conn, ukol_id, novy_stav)
    print(f"Stav úkolu ID {ukol_id} byl změněn na '{novy_stav}'.")


def odstranit_ukol(conn):
    """UI pro odstranění úkolu podle ID."""
    zobrazit_ukoly(conn)

    # výběr ID úkolu
    while True:
        vstup = input("Zadejte ID úkolu k odstranění: ").strip()
        try:
            ukol_id = int(vstup)
        except ValueError:
            print("Neplatný vstup. Zadejte celé číslo.")
            continue

        if db_najit_ukol(conn, ukol_id):  # úkol existuje
            break
        else:
            print(f"Úkol s ID {ukol_id} neexistuje. Zkuste to znovu.")

    db_odstranit_ukol(conn, ukol_id)
    print(f"Úkol ID {ukol_id} byl trvale odstraněn.")


def hlavni_menu(conn):
    """Hlavní smyčka programu - běží dokud uživatel nezvolí konec."""
    while True:
        print("\nSprávce úkolů - Hlavní menu")
        print("1. Přidat úkol")
        print("2. Zobrazit úkoly")
        print("3. Aktualizovat úkol")
        print("4. Odstranit úkol")
        print("5. Ukončit program")

        volba = input("Vyberte možnost (1-5): ").strip()

        if volba == "1":
            pridat_ukol(conn)
        elif volba == "2":
            zobrazit_ukoly(conn)
        elif volba == "3":
            aktualizovat_ukol(conn)
        elif volba == "4":
            odstranit_ukol(conn)
        elif volba == "5":
            print("Konec programu.")
            break  # ukončí hlavní smyčku
        else:
            print("Neplatná volba. Zadejte číslo od 1 do 5.")


if __name__ == "__main__":
    conn = pripojeni_db()
    if conn:
        vytvoreni_tabulky(conn)  # vytvoří tabulku pokud neexistuje
        hlavni_menu(conn)
        conn.close()  # uzavře připojení po skončení
