cube(`Orders`, {
  sql: `SELECT * FROM aura_gold.fct_sales`,

  measures: {
    count: {
      type: `count`
    },
    totalAmount: {
      sql: `amount_usd`,
      type: `sum`,
      format: `currency`
    },
    avgOrderValue: {
      sql: `amount_usd`,
      type: `avg`,
      format: `currency`
    },
    grossMargin: {
      sql: `gross_margin_usd`,
      type: `sum`,
      format: `currency`
    }
  },

  dimensions: {
    id: {
      sql: `order_id`,
      type: `number`,
      primaryKey: true
    },
    status: {
      sql: `order_status`,
      type: `string`
    },
    category: {
      sql: `category`,
      type: `string`
    },
    country: {
      sql: `country`,
      type: `string`
    },
    orderDate: {
      sql: `order_date`,
      type: `time`
    }
  }
});

