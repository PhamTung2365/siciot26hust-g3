#!/usr/bin/env python3
"""CLI enrollment and recognition using the same model/database as the web app."""

import os

import cv2

from face_db import add_face, delete_person, get_all_names, get_person_count, recognize_face
from face_utils import get_face_embedding


def embedding_from_image(image_path):
    if not os.path.isfile(image_path):
        print(f"✗ File not found: {image_path}")
        return None

    image = cv2.imread(image_path)
    if image is None:
        print(f"✗ Cannot read image: {image_path}")
        return None

    face, embedding = get_face_embedding(image)
    if face is None or embedding is None:
        print("✗ No face detected")
        return None
    return embedding


def enroll_face(image_path, person_name):
    embedding = embedding_from_image(image_path)
    if embedding is None:
        return False
    try:
        count = add_face(person_name.strip(), embedding)
    except ValueError as exc:
        print(f"✗ {exc}")
        return False
    print(f"✓ Enrolled: {person_name} ({count} embeddings)")
    return True


def recognize_image(image_path):
    embedding = embedding_from_image(image_path)
    if embedding is None:
        return False, "Unknown", 0.0
    name, confidence = recognize_face(embedding)
    print(f"[*] Best result: {name or 'Unknown'} ({confidence:.2%})")
    return name is not None, name or "Unknown", confidence


def print_menu():
    print("\nSmart Lock Face Recognition")
    print("1. Enroll new face")
    print("2. Recognize face")
    print("3. List registered people")
    print("4. Delete person")
    print("5. Exit")


def main():
    while True:
        print_menu()
        choice = input("Select option (1-5): ").strip()

        if choice == "1":
            enroll_face(input("Image path: ").strip(), input("Person name: ").strip())
        elif choice == "2":
            recognize_image(input("Image path: ").strip())
        elif choice == "3":
            names = get_all_names()
            print("\n".join(f"- {name} ({get_person_count(name)})" for name in names)
                  or "No people registered")
        elif choice == "4":
            name = input("Person name: ").strip()
            try:
                print("✓ Deleted" if delete_person(name) else "✗ Not found")
            except ValueError as exc:
                print(f"✗ {exc}")
        elif choice == "5":
            break
        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    main()
