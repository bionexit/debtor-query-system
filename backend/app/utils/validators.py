import re
from typing import Optional, Tuple


class PhoneValidator:
    """
    Phone number validator utility.
    """
    
    CHINA_MOBILE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
    INTERNATIONAL_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    
    @classmethod
    def validate_china_mobile(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Chinese mobile phone number.
        
        Returns:
            Tuple of (is_valid, normalized_phone or error_message)
        """
        if not phone:
            return False, "Phone number is required"
        
        phone = phone.strip()
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        if not cls.CHINA_MOBILE_PATTERN.match(phone):
            return False, "Invalid Chinese mobile phone number format"
        
        return True, phone
    
    @classmethod
    def validate_international(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate international phone number (E.164 format).
        
        Returns:
            Tuple of (is_valid, normalized_phone or error_message)
        """
        if not phone:
            return False, "Phone number is required"
        
        phone = phone.strip()
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        if not cls.INTERNATIONAL_PATTERN.match(phone):
            return False, "Invalid international phone number format"
        
        return True, phone
    
    @classmethod
    def validate(cls, phone: str, allow_international: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate phone number.
        
        Args:
            phone: The phone number string
            allow_international: Whether to allow international format
            
        Returns:
            Tuple of (is_valid, normalized_phone or error_message)
        """
        is_valid, result = cls.validate_china_mobile(phone)
        if is_valid:
            return True, result
        
        if allow_international:
            return cls.validate_international(phone)
        
        return False, result
    
    @classmethod
    def normalize(cls, phone: str) -> str:
        """
        Normalize phone number by removing formatting characters.
        """
        if not phone:
            return ''
        return ''.join(c for c in phone if c.isdigit() or c == '+')


class IDCardValidator:
    """
    Chinese ID card number validator.
    """
    
    WEIGHT_FACTORS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    CHECK_CODES = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    
    @classmethod
    def validate(cls, id_card: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Chinese ID card number (18-digit format).
        
        Returns:
            Tuple of (is_valid, error_message or None)
        """
        if not id_card:
            return False, "ID card number is required"
        
        id_card = id_card.strip().upper()
        
        if len(id_card) != 18:
            return False, "ID card number must be 18 digits"
        
        if not id_card[:17].isdigit():
            return False, "First 17 characters must be digits"
        
        if not id_card[17].isdigit() and id_card[17] != 'X':
            return False, "Last character must be a digit or X"
        
        calculated_sum = sum(int(id_card[i]) * cls.WEIGHT_FACTORS[i] for i in range(17))
        calculated_check = cls.CHECK_CODES[calculated_sum % 11]
        
        if calculated_check != id_card[17]:
            return False, "Invalid ID card check digit"
        
        return True, None


class BankAccountValidator:
    """
    Bank account number validator.
    """
    
    @classmethod
    def validate(cls, account: str) -> Tuple[bool, Optional[str]]:
        """
        Validate bank account number.
        
        Returns:
            Tuple of (is_valid, error_message or None)
        """
        if not account:
            return True, None
        
        account = account.strip()
        
        if len(account) < 10:
            return False, "Bank account number too short"
        
        if len(account) > 25:
            return False, "Bank account number too long"
        
        if not account.isdigit():
            return False, "Bank account must contain only digits"
        
        return True, None


class DebtorNumberValidator:
    """
    Debtor number validator.
    """
    
    PATTERN = re.compile(r'^[A-Z0-9\-_]{3,50}$')
    
    @classmethod
    def validate(cls, debtor_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate debtor number format.
        
        Returns:
            Tuple of (is_valid, error_message or None)
        """
        if not debtor_number:
            return False, "Debtor number is required"
        
        debtor_number = debtor_number.strip().upper()
        
        if not cls.PATTERN.match(debtor_number):
            return False, "Debtor number must be 3-50 alphanumeric characters, hyphens, or underscores"
        
        return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format.
    
    Returns:
        Tuple of (is_valid, error_message or None)
    """
    if not email:
        return True, None
    
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if not pattern.match(email.strip()):
        return False, "Invalid email format"
    
    return True, None
