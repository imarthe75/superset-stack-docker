cube(`Users`, {
    sql: `SELECT * FROM public.users`,

    measures: {
        count: {
            type: `count`
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
        country: {
            sql: `country`,
            type: `string`
        },
        createdAt: {
            sql: `created_at`,
            type: `time`
        }
    }
});
