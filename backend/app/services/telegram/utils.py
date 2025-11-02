"""
Utility functions for Telegram bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_button():
    """Create inline keyboard with back to main button"""
    keyboard = [[InlineKeyboardButton("🏠 Back to Main", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)
