/**
 * Spanish (ES) Translations
 */
export const es = {
    common: {
        login: 'Entrar',
        logout: 'Salir',
        getStarted: 'Empezar',
        features: 'Funcionalidades',
        pricing: 'Precios',
        security: 'Seguridad',
        resources: 'Recursos',
        legal: 'Legal',
        loading: 'Cargando...',
        contactSales: 'Contactar con Ventas',
        startFree: 'Empezar Gratis',
    },
    landing: {
        hero: {
            badge: 'SaaS de Grado Industrial',
            titlePrimary: 'El Gateway',
            titleSecondary: 'Definitivo',
            titleTertiary: 'para Sistemas Ajax',
            description: 'Monitoriza, controla y gestiona tu infraestructura de seguridad de forma segura con un SaaS de grado industrial. Integración de latencia cero para instaladores profesionales y gestores de empresas.',
            ctaStart: 'Iniciar Despliegue',
            ctaDemo: 'Ver Demo',
            encrypted: 'Encriptado',
            distributed: 'Distribuido',
            realtime: 'Tiempo Real',
        },
        capabilities: {
            tag: 'Capacidades',
            title: 'Funcionalidades Avanzadas',
            description: 'Nuestro gateway proporciona las herramientas de alto rendimiento necesarias para infraestructuras de seguridad de misión crítica.',
            items: [
                { title: 'Integración API', desc: 'Conecta tu entorno industrial sin interrupciones con nuestra robusta API para desarrolladores. Arquitectura Restful con documentación extensiva.', icon: '🔗' },
                { title: 'Telemetría en Tiempo Real', desc: 'Monitoriza la salud de los dispositivos, niveles de batería y fuerza de señal con latencia cero y precisión de grado industrial.', icon: '📊' },
                { title: 'Proxy Inteligente', desc: 'Enrutamiento seguro para cada petición a través de nuestra capa de proxy propietaria, asegurando que el hardware permanezca invisible en la red pública.', icon: '🔐' }
            ]
        },
        security: {
            title: 'Seguridad y',
            titleHighlight: 'Cumplimiento',
            titleSuffix: 'en cada Capa',
            description: 'Nuestra plataforma está diseñada para cumplir con los estándares más exigentes, asegurando que tus datos de seguridad más sensibles se gestionen con integridad criptográfica.',
            items: [
                { title: 'Registros de Auditoría Detallados', desc: 'Historial completo y evidente ante manipulaciones de cada acción realizada en tu red de seguridad.' },
                { title: 'Autenticación JWT', desc: 'Sesión de autenticación segura basada en tokens que garantiza un acceso estrictamente autorizado a tus endpoints.' },
                { title: 'Cumplimiento GDPR e ISO', desc: 'Marcos de privacidad de datos integrados para mantener los datos de tus clientes gestionados y legalmente conformes.' }
            ]
        },
        pricing: {
            tag: 'Planes de Precios',
            title: 'Escala tu Seguridad',
            plans: [
                {
                    name: 'Uso Personal',
                    price: '$0',
                    period: '/ para siempre',
                    desc: 'Perfecto para propietarios individuales que prueban el gateway.',
                    features: ['1 Dispositivo Activo', 'Telemetría Básica (Sin refresco)', 'Soporte de la Comunidad (Discord)']
                },
                {
                    name: 'Pro Industrial',
                    recommended: 'RECOMENDADO PARA PROFESIONALES',
                    price: 'Personalizado',
                    period: '/ basado en volumen',
                    desc: 'Diseñado para instaladores que gestionan múltiples sitios de alta gama.',
                    features: [
                        'Hubs y Dispositivos Ilimitados',
                        'Flujo de Telemetría en Tiempo Real',
                        'Acceso Avanzado a API y Webhooks',
                        'Pagos Integrados con Stripe',
                        'Soporte de Cupones AJAX-XXX-X',
                        'Soporte SLA Prioritario 24/7'
                    ]
                }
            ]
        },
        footer: {
            tagline: 'Conectando el hardware de seguridad más fiable del mundo con la infraestructura de software moderna. Proxy de grado industrial para sistemas Ajax.',
            resources: ['Documentación API', 'Estado del Sistema', 'Centro de Soporte'],
            legal: ['Política de Privacidad', 'Términos de Servicio', 'Divulgación de Seguridad'],
            copyright: '© 2024 AjaxSecurFlow Inc. No afiliado con Ajax Systems Ltd. Todos los derechos reservados.'
        }
    },
    auth: {
        title: 'Acceso al Gateway',
        instruction: 'IMPORTANTE: Utiliza exactamente el mismo email y contraseña que usas para entrar en tu aplicación AJAX SECURITY.',
        emailLabel: 'Email de tu cuenta AJAX',
        passwordLabel: 'Contraseña',
        loginButton: 'Entrar al Panel',
        loggingIn: 'Entrando...',
        noAccount: '¿No tienes cuenta?',
        requestAccess: 'Solicita acceso',
        errorTitle: 'Error al iniciar sesión',
        errorDetail: 'Verifica tus credenciales de Ajax.'
    },
    dashboard: {
        title: 'Panel Principal',
        searchPlaceholder: 'Buscar dispositivos, hubs o registros...',
        systemStatus: {
            secure: 'Sistema Seguro',
            attention: 'Atención Requerida'
        },
        nav: {
            dashboard: 'Escritorio',
            devices: 'Dispositivos',
            notifications: 'Notificaciones',
            subscription: 'Facturación',
            settings: 'Configuración',
            support: 'Soporte',
            logout: 'Cerrar Sesión'
        },
        stats: {
            activeHubs: 'Hubs Activos',
            securityAlerts: 'Alertas de Seguridad',
            connectivity: 'Conectividad',
            planStatus: 'Estado del Plan',
            allSystemsOnline: 'Todos los sistemas en línea',
            systemDegraded: 'Sistema degradado',
            past24h: 'Últimas 24h',
            uptime: 'Tiempos de actividad',
            active: 'Activo',
            manageBilling: 'GESTIONAR FACTURACIÓN'
        },
        hubs: {
            title: 'Estado de Hubs Activos',
            viewAll: 'Ver todos los dispositivos'
        },
        telemetry: {
            title: 'Telemetría del Dispositivo',
            viewFullLogs: 'Ver Historial Completo',
            labels: {
                name: 'Nombre del Dispositivo',
                status: 'Estado',
                battery: 'Batería',
                signal: 'Señal',
                temp: 'Temp',
                action: 'Acción',
                details: 'Detalles'
            }
        },
        events: {
            title: 'Flujo de Eventos',
            live: 'En Vivo'
        }
    }
}

export type Translations = typeof es
