import stripe


class StripeService:

    @staticmethod
    def create_product(name, description=None):
        """Создает продукт в Stripe"""
        try:
            product_data = {
                "name": name,
                "description": description or f"Product: {name}",
            }

            product = stripe.Product.create(**product_data)
            return product

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe product creation error: {str(e)}")

    @staticmethod
    def create_price(product_id, amount, currency="usd"):
        """Создает цену в Stripe"""
        try:
            price_data = {
                "product": product_id,
                "unit_amount": int(amount * 100),
                "currency": currency.lower(),
            }

            price = stripe.Price.create(**price_data)
            return price

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe price creation error: {str(e)}")

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url):
        """Создает сессию checkout в Stripe"""
        try:
            session_data = {
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
            }

            session = stripe.checkout.Session.create(**session_data)
            return session

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe session creation error: {str(e)}")
