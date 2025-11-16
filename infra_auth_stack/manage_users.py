#!/usr/bin/env python3
"""
User Management Script for Auth Stack

This script helps you add/list/delete users in the DynamoDB users table.

Usage:
    # Add a user
    python manage_users.py add --username john_doe --password secret123 --email john@example.com

    # List all users
    python manage_users.py list

    # Delete a user
    python manage_users.py delete --username john_doe
"""

import argparse
import hashlib
import boto3
from datetime import datetime
from typing import Optional


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def add_user(
    table_name: str,
    username: str,
    password: str,
    email: Optional[str] = None,
    region: str = "us-west-2",
) -> None:
    """Add a new user to the DynamoDB table"""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    try:
        # Check if user already exists
        response = table.get_item(Key={"username": username})
        if "Item" in response:
            print(f"❌ User '{username}' already exists!")
            return

        # Add new user
        password_hash = hash_password(password)
        item = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
        }

        if email:
            item["email"] = email

        table.put_item(Item=item)
        print(f"✅ User '{username}' created successfully!")
        print(f"   Email: {email or 'N/A'}")

    except Exception as e:
        print(f"❌ Error adding user: {str(e)}")


def list_users(table_name: str, region: str = "us-west-2") -> None:
    """List all users in the DynamoDB table"""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    try:
        response = table.scan()
        items = response.get("Items", [])

        if not items:
            print("📭 No users found in the table")
            return

        print(f"\n👥 Found {len(items)} user(s):\n")
        print(f"{'Username':<20} {'Email':<30} {'Created At':<25}")
        print("-" * 75)

        for item in items:
            username = item.get("username", "N/A")
            email = item.get("email", "N/A")
            created_at = item.get("created_at", "N/A")
            print(f"{username:<20} {email:<30} {created_at:<25}")

    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")


def delete_user(table_name: str, username: str, region: str = "us-west-2") -> None:
    """Delete a user from the DynamoDB table"""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    try:
        # Check if user exists
        response = table.get_item(Key={"username": username})
        if "Item" not in response:
            print(f"❌ User '{username}' not found!")
            return

        # Confirm deletion
        confirm = input(
            f"⚠️  Are you sure you want to delete user '{username}'? (yes/no): "
        )
        if confirm.lower() != "yes":
            print("❌ Deletion cancelled")
            return

        # Delete user
        table.delete_item(Key={"username": username})
        print(f"✅ User '{username}' deleted successfully!")

    except Exception as e:
        print(f"❌ Error deleting user: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage users in the Auth Stack DynamoDB table"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add user command
    add_parser = subparsers.add_parser("add", help="Add a new user")
    add_parser.add_argument("--username", required=True, help="Username")
    add_parser.add_argument("--password", required=True, help="Password")
    add_parser.add_argument("--email", help="Email address (optional)")
    add_parser.add_argument(
        "--table-name",
        default="prod-users-table-969341425463",
        help="DynamoDB table name",
    )
    add_parser.add_argument(
        "--region",
        default="eu-west-3",
        help="AWS region",
    )

    # List users command
    list_parser = subparsers.add_parser("list", help="List all users")
    list_parser.add_argument(
        "--table-name",
        default="prod-users-table-969341425463",
        help="DynamoDB table name",
    )
    list_parser.add_argument(
        "--region",
        default="eu-west-3",
        help="AWS region",
    )

    # Delete user command
    delete_parser = subparsers.add_parser("delete", help="Delete a user")
    delete_parser.add_argument("--username", required=True, help="Username to delete")
    delete_parser.add_argument(
        "--table-name",
        default="prod-users-table-969341425463",
        help="DynamoDB table name",
    )
    delete_parser.add_argument(
        "--region",
        default="eu-west-3",
        help="AWS region",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get the full table name (it will have account ID suffix after deployment)
    # You can find this in the CloudFormation outputs
    # For now, we'll use the provided table name
    table_name = args.table_name

    if args.command == "add":
        add_user(table_name, args.username, args.password, args.email, args.region)
    elif args.command == "list":
        list_users(table_name, args.region)
    elif args.command == "delete":
        delete_user(table_name, args.username, args.region)


if __name__ == "__main__":
    main()
