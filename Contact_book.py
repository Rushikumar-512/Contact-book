import json
import os
import re
from typing import Dict, Any, List

DATA_FILE = "contacts.json"

PHONE_RE = re.compile(r"^\+?\d{7,15}$")  # allows optional + and 7-15 digits
EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def load_contacts() -> Dict[str, Dict[str, Any]]:
    """Load contacts from DATA_FILE. Returns a dict keyed by contact id (string)."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            # if old file format (list), convert to dict
            if isinstance(data, list):
                return {c.get("id", str(i)): c for i, c in enumerate(data)}
    except (json.JSONDecodeError, OSError):
        print("Warning: contacts file corrupted or unreadable. Starting fresh.")
    return {}


def save_contacts(contacts: Dict[str, Dict[str, Any]]) -> None:
    """Write contacts dict to DATA_FILE atomically."""
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def generate_id(contacts: Dict[str, Dict[str, Any]]) -> str:
    """Generate a new unique string id."""
    i = 1
    while str(i) in contacts:
        i += 1
    return str(i)


def validate_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone.strip()))


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def prompt_non_empty(prompt_text: str) -> str:
    while True:
        val = input(prompt_text).strip()
        if val:
            return val
        print("Input cannot be empty.")


def add_contact(contacts: Dict[str, Dict[str, Any]]) -> None:
    print("\n--- Add Contact ---")
    name = prompt_non_empty("Name: ")
    phone = input("Phone (digits, optional +): ").strip()
    if phone and not validate_phone(phone):
        print("Invalid phone format. It should be 7-15 digits, optional leading +. Save without phone? (y/N)")
        if input("> ").lower() != "y":
            print("Cancelled add.")
            return
    email = input("Email: ").strip()
    if email and not validate_email(email):
        print("Invalid email format. Save without email? (y/N)")
        if input("> ").lower() != "y":
            print("Cancelled add.")
            return
    address = input("Address (optional): ").strip()
    notes = input("Notes (optional): ").strip()

    cid = generate_id(contacts)
    contacts[cid] = {
        "id": cid,
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "notes": notes,
    }
    save_contacts(contacts)
    print(f"Contact '{name}' added with id {cid}.")


def list_contacts(contacts: Dict[str, Dict[str, Any]]) -> None:
    if not contacts:
        print("\nNo contacts found.")
        return
    print("\n--- All Contacts ---")
    # sort by name
    sorted_list = sorted(contacts.values(), key=lambda c: c.get("name", "").lower())
    for c in sorted_list:
        print(f"[{c['id']}] {c.get('name')}  |  {c.get('phone','-')}  |  {c.get('email','-')}")


def show_contact(contact: Dict[str, Any]) -> None:
    print("\n----------------------------")
    print(f"ID:      {contact.get('id')}")
    print(f"Name:    {contact.get('name')}")
    print(f"Phone:   {contact.get('phone') or '-'}")
    print(f"Email:   {contact.get('email') or '-'}")
    print(f"Address: {contact.get('address') or '-'}")
    print(f"Notes:   {contact.get('notes') or '-'}")
    print("----------------------------")


def view_contact(contacts: Dict[str, Dict[str, Any]]) -> None:
    cid = input("Enter contact id to view (or press Enter to search by name): ").strip()
    if cid:
        c = contacts.get(cid)
        if not c:
            print("Contact id not found.")
            return
        show_contact(c)
        return

    term = input("Search name / phone / email: ").strip().lower()
    if not term:
        print("Empty search.")
        return
    results = [
        c for c in contacts.values()
        if term in (c.get("name","").lower() + " " + c.get("phone","") + " " + c.get("email","").lower())
    ]
    if not results:
        print("No matching contacts.")
        return
    print(f"Found {len(results)} result(s):")
    for c in results:
        show_contact(c)


def update_contact(contacts: Dict[str, Dict[str, Any]]) -> None:
    cid = input("Enter contact id to update: ").strip()
    if not cid or cid not in contacts:
        print("Invalid or missing id.")
        return
    contact = contacts[cid]
    print("Press Enter to keep current value.")
    new_name = input(f"Name [{contact.get('name')}]: ").strip()
    if new_name:
        contact["name"] = new_name
    new_phone = input(f"Phone [{contact.get('phone') or '-'}]: ").strip()
    if new_phone:
        if validate_phone(new_phone):
            contact["phone"] = new_phone
        else:
            print("Invalid phone format. Keeping old phone.")
    new_email = input(f"Email [{contact.get('email') or '-'}]: ").strip()
    if new_email:
        if validate_email(new_email):
            contact["email"] = new_email
        else:
            print("Invalid email. Keeping old email.")
    new_address = input(f"Address [{contact.get('address') or '-'}]: ").strip()
    if new_address:
        contact["address"] = new_address
    new_notes = input(f"Notes [{contact.get('notes') or '-'}]: ").strip()
    if new_notes:
        contact["notes"] = new_notes

    contacts[cid] = contact
    save_contacts(contacts)
    print("Contact updated.")


def delete_contact(contacts: Dict[str, Dict[str, Any]]) -> None:
    cid = input("Enter contact id to delete: ").strip()
    if not cid or cid not in contacts:
        print("Invalid or missing id.")
        return
    show_contact(contacts[cid])
    confirm = input(f"Are you sure you want to delete '{contacts[cid]['name']}'? (y/N): ").lower()
    if confirm == "y":
        del contacts[cid]
        save_contacts(contacts)
        print("Deleted.")
    else:
        print("Cancelled.")


def import_contacts(contacts: Dict[str, Dict[str, Any]]) -> None:
    path = input("Enter path to JSON file to import (list or dict): ").strip()
    if not os.path.exists(path):
        print("File doesn't exist.")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Failed to read file:", e)
        return

    added = 0
    if isinstance(data, dict):
        for k, v in data.items():
            nid = generate_id(contacts)
            v["id"] = nid
            contacts[nid] = v
            added += 1
    elif isinstance(data, list):
        for item in data:
            nid = generate_id(contacts)
            item["id"] = nid
            contacts[nid] = item
            added += 1
    else:
        print("Unsupported format.")
        return

    save_contacts(contacts)
    print(f"Imported {added} contacts.")


def export_contacts(contacts: Dict[str, Dict[str, Any]]) -> None:
    path = input("Enter file path to export contacts to (e.g. export.json): ").strip()
    if not path:
        print("No path given.")
        return
    # Export as list for portability
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(contacts.values()), f, indent=2, ensure_ascii=False)
    print(f"Exported {len(contacts)} contacts to {path}.")


def menu() -> None:
    contacts = load_contacts()
    actions = {
        "1": ("Add contact", add_contact),
        "2": ("List contacts", list_contacts),
        "3": ("View / Search contact", view_contact),
        "4": ("Update contact", update_contact),
        "5": ("Delete contact", delete_contact),
        "6": ("Import contacts from JSON", import_contacts),
        "7": ("Export contacts to JSON", export_contacts),
        "0": ("Exit", None),
    }

    while True:
        print("\n=== Contact Book ===")
        for k, (desc, _) in actions.items():
            print(f"{k}. {desc}")
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if not action:
            print("Invalid option.")
            continue
        _, func = action
        try:
            func(contacts)
        except Exception as e:
            print("An error occurred:", e)


if __name__ == "__main__":
    menu()
