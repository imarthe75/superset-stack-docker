cube(`MlPrediccionVentas`, {
    sql: `SELECT * FROM public.ml_prediccion_ventas`,

    measures: {
        count: {
            type: `count`,
            drillMembers: [modeloVersion, fechaPrediccion]
        },

        totalPrediccion: {
            sql: `prediccion_ventas`,
            type: `sum`
        },

        promedioPrediccion: {
            sql: `prediccion_ventas`,
            type: `avg`
        }
    },

    dimensions: {
        fechaPrediccion: {
            sql: `fecha_prediccion`,
            type: `time`
        },

        mesSimulado: {
            sql: `mes_simulado`,
            type: `number`
        },

        modeloVersion: {
            sql: `modelo_version`,
            type: `string`
        },

        id: {
            sql: `mes_simulado`, # Usamos mes_simulado como pseudo- id para esta tabla simple
      type: `number`,
        primaryKey: true
    }
},

    dataSource: `default`
});
