"""
Transaction service for managing financial transactions.

This module provides business logic for transaction operations including
CRUD operations, categorization, and transaction analytics.
"""

import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, UTC
import csv
import io

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from ..models import db, Transaction, TransactionType, TransactionCategory, Account

logger = logging.getLogger(__name__)


class TransactionService:
    """Service class for managing financial transactions."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the transaction service.
        
        Args:
            session: Database session (uses db.session if not provided)
        """
        self.session = session or db.session
    
    def create_transaction(
        self,
        account_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        transaction_date: date,
        category: TransactionCategory = TransactionCategory.UNCATEGORIZED,
        payee: Optional[str] = None,
        reference: Optional[str] = None,
        tags: Optional[str] = None,
        is_recurring: bool = False,
        notes: Optional[str] = None,
        update_balance: bool = True
    ) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            account_id: ID of the associated account
            amount: Transaction amount
            transaction_type: Type of transaction
            description: Transaction description
            transaction_date: Date of transaction
            category: Transaction category
            payee: Payee name
            reference: Reference number
            tags: Comma-separated tags
            is_recurring: Whether transaction is recurring
            notes: Additional notes
            update_balance: Whether to update account balance
            
        Returns:
            Created transaction instance
        """
        try:
            transaction = Transaction(
                account_id=account_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                date=transaction_date,
                category=category,
                payee=payee,
                reference=reference,
                tags=tags,
                is_recurring=is_recurring,
                notes=notes
            )
            
            self.session.add(transaction)
            
            # Update account balance if requested
            if update_balance:
                account = self.session.query(Account).filter(Account.id == account_id).first()
                if account:
                    account.update_balance(amount)
            
            self.session.commit()
            
            logger.info(f"Created transaction: {description} for ${amount}")
            return transaction
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating transaction: {e}")
            raise
    
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction instance or None if not found
        """
        return self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_transactions(
        self,
        account_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None,
        category: Optional[TransactionCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        payee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transactions with optional filtering.
        
        Args:
            account_id: Filter by account ID
            transaction_type: Filter by transaction type
            category: Filter by category
            start_date: Filter by start date
            end_date: Filter by end date
            payee: Filter by payee
            tags: Filter by tags
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of transactions matching criteria
        """
        query = self.session.query(Transaction)
        
        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)
        
        if transaction_type is not None:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        if category is not None:
            query = query.filter(Transaction.category == category)
        
        if start_date is not None:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date is not None:
            query = query.filter(Transaction.date <= end_date)
        
        if payee is not None:
            query = query.filter(Transaction.payee.ilike(f'%{payee}%'))
        
        if tags:
            # Filter by any of the provided tags
            tag_filters = [Transaction.tags.ilike(f'%{tag}%') for tag in tags]
            query = query.filter(or_(*tag_filters))
        
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        
        if offset > 0:
            query = query.offset(offset)
        
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
    
    def update_transaction(
        self,
        transaction_id: int,
        update_balance: bool = True,
        **kwargs
    ) -> Optional[Transaction]:
        """
        Update transaction information.
        
        Args:
            transaction_id: Transaction ID
            update_balance: Whether to update account balance
            **kwargs: Fields to update
            
        Returns:
            Updated transaction or None if not found
        """
        try:
            transaction = self.get_transaction(transaction_id)
            if not transaction:
                return None
            
            old_amount = transaction.amount
            old_account_id = transaction.account_id
            
            # Update allowed fields
            allowed_fields = {
                'amount', 'transaction_type', 'description', 'date',
                'category', 'payee', 'reference', 'tags', 'notes'
            }
            
            for key, value in kwargs.items():
                if key in allowed_fields and hasattr(transaction, key):
                    setattr(transaction, key, value)
            
            transaction.updated_at = datetime.now(UTC)
            
            # Update account balance if amount or account changed
            if update_balance and ('amount' in kwargs or 'account_id' in kwargs):
                # Reverse old transaction
                old_account = self.session.query(Account).filter(Account.id == old_account_id).first()
                if old_account:
                    old_account.update_balance(-old_amount)
                
                # Apply new transaction
                new_account_id = kwargs.get('account_id', old_account_id)
                new_account = self.session.query(Account).filter(Account.id == new_account_id).first()
                if new_account:
                    new_account.update_balance(transaction.amount)
            
            self.session.commit()
            
            logger.info(f"Updated transaction {transaction_id}")
            return transaction
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise
    
    def delete_transaction(self, transaction_id: int, update_balance: bool = True) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction ID
            update_balance: Whether to update account balance
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            transaction = self.get_transaction(transaction_id)
            if not transaction:
                return False
            
            # Update account balance by reversing the transaction
            if update_balance:
                account = self.session.query(Account).filter(Account.id == transaction.account_id).first()
                if account:
                    account.update_balance(-transaction.amount)
            
            self.session.delete(transaction)
            self.session.commit()
            
            logger.info(f"Deleted transaction {transaction_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise
    
    def get_transaction_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get transaction summary statistics.
        
        Args:
            start_date: Start date for summary
            end_date: End date for summary
            account_id: Filter by account ID
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            query = self.session.query(Transaction)
            
            if account_id is not None:
                query = query.filter(Transaction.account_id == account_id)
            
            if start_date is not None:
                query = query.filter(Transaction.date >= start_date)
            
            if end_date is not None:
                query = query.filter(Transaction.date <= end_date)
            
            # Get income and expense totals
            income_total = (
                query.filter(Transaction.amount > 0)
                .with_entities(func.sum(Transaction.amount))
                .scalar() or Decimal('0')
            )
            
            expense_total = (
                query.filter(Transaction.amount < 0)
                .with_entities(func.sum(Transaction.amount))
                .scalar() or Decimal('0')
            )
            
            # Get transaction counts by type
            type_counts = (
                query.with_entities(
                    Transaction.transaction_type,
                    func.count(Transaction.id)
                )
                .group_by(Transaction.transaction_type)
                .all()
            )
            
            # Get spending by category
            category_spending = (
                query.filter(Transaction.amount < 0)
                .with_entities(
                    Transaction.category,
                    func.sum(Transaction.amount)
                )
                .group_by(Transaction.category)
                .all()
            )
            
            return {
                'total_income': income_total,
                'total_expenses': abs(expense_total),
                'net_income': income_total + expense_total,  # expense_total is negative
                'transaction_counts': {t_type.value: count for t_type, count in type_counts},
                'category_spending': {category.value: abs(amount) for category, amount in category_spending},
                'total_transactions': query.count()
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            return {
                'total_income': Decimal('0'),
                'total_expenses': Decimal('0'),
                'net_income': Decimal('0'),
                'transaction_counts': {},
                'category_spending': {},
                'total_transactions': 0
            }

    def import_from_csv(
        self,
        csv_content: str,
        account_id: int,
        column_mapping: Optional[Dict[str, str]] = None,
        skip_header: bool = True
    ) -> Tuple[int, List[str]]:
        """
        Import transactions from CSV content.

        Args:
            csv_content: CSV content as string
            account_id: Account ID to associate transactions with
            column_mapping: Mapping of CSV columns to transaction fields
            skip_header: Whether to skip the first row

        Returns:
            Tuple of (imported_count, error_messages)
        """
        default_mapping = {
            'description': 'description',
            'amount': 'amount',
            'date': 'date',
            'category': 'category',
            'payee': 'payee',
            'reference': 'reference',
            'notes': 'notes'
        }

        mapping = column_mapping or default_mapping
        imported_count = 0
        errors = []

        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            # Normalize column names (case-insensitive)
            normalized_fieldnames = {name.lower(): name for name in csv_reader.fieldnames}

            for row_num, row in enumerate(csv_reader, start=2 if skip_header else 1):
                try:
                    # Normalize row keys
                    normalized_row = {key.lower(): value for key, value in row.items()}

                    # Extract required fields
                    description = self._get_csv_value(normalized_row, mapping.get('description', 'description'), normalized_fieldnames)
                    amount_str = self._get_csv_value(normalized_row, mapping.get('amount', 'amount'), normalized_fieldnames)
                    date_str = self._get_csv_value(normalized_row, mapping.get('date', 'date'), normalized_fieldnames)

                    if not all([description, amount_str, date_str]):
                        errors.append(f"Row {row_num}: Missing required fields (description, amount, date)")
                        continue

                    # Parse amount
                    amount = Decimal(amount_str.replace('$', '').replace(',', ''))

                    # Parse date
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Determine transaction type
                    transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE

                    # Get optional fields
                    category_str = self._get_csv_value(normalized_row, mapping.get('category', 'category'), normalized_fieldnames)
                    category = self._parse_category(category_str) if category_str else TransactionCategory.UNCATEGORIZED

                    payee = self._get_csv_value(normalized_row, mapping.get('payee', 'payee'), normalized_fieldnames)
                    reference = self._get_csv_value(normalized_row, mapping.get('reference', 'reference'), normalized_fieldnames)
                    notes = self._get_csv_value(normalized_row, mapping.get('notes', 'notes'), normalized_fieldnames)

                    # Create transaction
                    self.create_transaction(
                        account_id=account_id,
                        amount=amount,
                        transaction_type=transaction_type,
                        description=description,
                        transaction_date=transaction_date,
                        category=category,
                        payee=payee,
                        reference=reference,
                        notes=notes,
                        update_balance=True
                    )

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue

            logger.info(f"Imported {imported_count} transactions from CSV")
            return imported_count, errors

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return 0, [f"CSV import failed: {str(e)}"]

    def export_to_csv(
        self,
        transactions: List[Transaction],
        include_headers: bool = True
    ) -> str:
        """
        Export transactions to CSV format.

        Args:
            transactions: List of transactions to export
            include_headers: Whether to include column headers

        Returns:
            CSV content as string
        """
        output = io.StringIO()

        fieldnames = [
            'date', 'description', 'amount', 'category', 'transaction_type',
            'payee', 'reference', 'account_name', 'notes'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)

        if include_headers:
            writer.writeheader()

        for transaction in transactions:
            writer.writerow({
                'date': transaction.date.isoformat(),
                'description': transaction.description,
                'amount': str(transaction.amount),
                'category': transaction.category.value,
                'transaction_type': transaction.transaction_type.value,
                'payee': transaction.payee or '',
                'reference': transaction.reference or '',
                'account_name': transaction.account.name if transaction.account else '',
                'notes': transaction.notes or ''
            })

        return output.getvalue()

    def _get_csv_value(self, row: Dict[str, str], field_name: str, normalized_fieldnames: Dict[str, str]) -> Optional[str]:
        """Get value from CSV row with case-insensitive field matching."""
        normalized_field = field_name.lower()
        if normalized_field in normalized_fieldnames:
            actual_field = normalized_fieldnames[normalized_field]
            return row.get(normalized_field, '').strip() or None
        return None

    def _parse_category(self, category_str: str) -> TransactionCategory:
        """Parse category string to TransactionCategory enum."""
        try:
            # Try exact match first
            return TransactionCategory(category_str.lower())
        except ValueError:
            # Try to find a close match
            category_lower = category_str.lower()
            for category in TransactionCategory:
                if category_lower in category.value or category.value in category_lower:
                    return category
            return TransactionCategory.UNCATEGORIZED
