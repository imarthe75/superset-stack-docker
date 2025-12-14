cube(`VentasHistoricas`, {
    sql: `SELECT * FROM public.ventas_historicas`,

    measures: {
        count: {
            type: `count`
        },

        totalVentas: {
            sql: `ventas_reales`,
            type: `sum`
        },

        promedioVentas: {
            sql: `ventas_reales`,
            type: `avg`
        }
    },

    dimensions: {
        historicoMes: {
            sql: `historico_mes`,
            type: `number`,
            primaryKey: true
        }
    },

    dataSource: `default`
});
