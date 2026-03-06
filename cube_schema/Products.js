cube(`Products`, {
    sql: `SELECT * FROM public.products`,

    measures: {
        count: {
            type: `count`
        },
        avgPrice: {
            sql: `price`,
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
        name: {
            sql: `name`,
            type: `string`
        },
        category: {
            sql: `category`,
            type: `string`
        }
    }
});
