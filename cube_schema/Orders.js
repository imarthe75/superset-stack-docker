cube(`Orders`, {
    sql: `SELECT * FROM public.orders`,

    joins: {
        Users: {
            sql: `${CUBE}.user_id = ${Users}.id`,
            relationship: `belongsTo`
        },
        Products: {
            sql: `${CUBE}.product_id = ${Products}.id`,
            relationship: `belongsTo`
        }
    },

    measures: {
        count: {
            type: `count`,
            draggable: true,
        },
        totalAmount: {
            sql: `amount`,
            type: `sum`,
            format: `currency`
        },
        avgOrderValue: {
            sql: `amount`,
            type: `avg`,
            format: `currency`
        }
    },

    dimensions: {
        id: {
            sql: `id`,
            type: `number`,
            primaryKey: true
        },
        status: {
            sql: `status`,
            type: `string`
        },
        orderDate: {
            sql: `order_date`,
            type: `time`
        }
    }
});
