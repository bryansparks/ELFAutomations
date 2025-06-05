"""
Example distributed agents demonstrating the CrewAI + A2A architecture.
"""

from .sales_agent import SalesAgent
from .marketing_agent import MarketingAgent
from .customer_success_agent import CustomerSuccessAgent

__all__ = [
    "SalesAgent",
    "MarketingAgent", 
    "CustomerSuccessAgent"
]
