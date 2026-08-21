CREATE OR REFRESH MATERIALIZED VIEW cart_abandoned_with_email
COMMENT "Abandoned carts enriched with customer contact info and a reminder email."
TBLPROPERTIES ("quality" = "gold")
AS SELECT
  c.cart_id,
  c.user_id,
  c.source_timestamp,
  c.items,
  s.first_name,
  s.surname,
  s.email,
  'Complete your purchase at the Bosch Powertools Shop' AS subject,
  CONCAT(
    'Hello ', COALESCE(s.first_name, ''), ' ', COALESCE(s.surname, ''), ',\n',
    '\n',
    'We noticed you left some items in your cart.\n',
    '\n',
    'Your cart contains:\n',
    ARRAY_JOIN(TRANSFORM(c.items, x -> CONCAT('  - ', x.quantity, ' x ', x.item_name, ' @ ', FORMAT_NUMBER(x.price, 2), ' ', x.currency)), '\n'),
    '\n\n',
    'Would you like to complete your purchase? Simply visit your cart to check out.\n',
    '\n',
    'See you soon,\n',
    'The Bosch Powertools Shop Team'
  ) AS body
FROM cart_abandoned c
INNER JOIN event_sign_up s ON c.user_id = s.user_id
