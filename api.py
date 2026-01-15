class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    customer_email = Column(String, nullable=False, index=True)
    customer_name = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, index=True)

    stripe_payment_id = Column(String, unique=True, index=True, nullable=True)
    stripe_customer_id = Column(String, index=True, nullable=True)
    amount_paid = Column(Float, nullable=True)
    currency = Column(String, default="USD")

    topic = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    tone = Column(String, nullable=True)

    status = Column(
        SAEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False
    )

    # ✅ THIS is what your broken line should be
    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)

    wordpress_site_url = Column(String, nullable=True)
    wordpress_post_id = Column(String, nullable=True)
    wordpress_post_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
