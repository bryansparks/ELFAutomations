"""
Example distributed agents demonstrating the CrewAI + A2A architecture.
"""

from .customer_success_agent import CustomerSuccessAgent
from .marketing_agent import MarketingAgent
from .sales_agent import SalesAgent

__all__ = ["SalesAgent", "MarketingAgent", "CustomerSuccessAgent"]
