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
            secure: 'Sistemas Online',
            attention: 'Atención Requerida',
            degraded: 'Sistema Degradado'
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
        profile: {
            adminUser: 'Usuario no definido',
            role: 'Ajax Systems Pro'
        },
        stats: {
            activeHubs: 'Hubs Activos',
            planStatus: 'Estado del Plan',
            allSystemsOnline: 'Todos los sistemas en línea',
            systemDegraded: 'Sistema degradado',
            past24h: 'Últimas 24h',
            uptime: 'Tiempos de actividad',
            active: 'Activo',
            expired: 'Expirado / Inactivo',
            manageBilling: 'GESTIONAR FACTURACIÓN',
            premium: 'Premium',
            pro: 'Pro',
            basic: 'Básico',
            free: 'Gratuito',
        },
        hubs: {
            title: 'Estado de Hubs Activos',
            viewAll: 'Ver todos los dispositivos',
            empty: 'No se encontraron Hubs activos',
            emptyHint: 'Asegúrate de tener dispositivos en tu cuenta Ajax.',
            status: {
                armed: 'Armado',
                disarmed: 'Desarmado',
                night: 'Modo Noche',
                online: 'Hub Conectado',
                offline: 'Hub Desconectado'
            },
            telemetry: {
                connection: 'Conexión',
                signal: 'Señal',
                battery: 'Batería',
                excellent: 'Excelente',
                sending: 'Enviando...',
                armTotal: '🛡️ Armado Total',
                disarm: '🔓 Desarmar',
                nightMode: '🌙 Modo Noche'
            }
        },
        profilePage: {
            title: 'Perfil de Usuario',
            personalInfo: 'Información Personal',
            notifications: 'Configuración de Notificaciones',
            emailNotifications: 'Notificaciones por Email',
            emailDescription: 'Recibe alertas críticas de seguridad directamente en tu bandeja de entrada.',
            saveChanges: 'Guardar Cambios',
            success: 'Perfil actualizado correctamente',
            labels: {
                firstName: 'Nombre',
                lastName: 'Apellidos',
                email: 'Correo Electrónico',
                phone: 'Teléfono',
                role: 'Rol de Sistema'
            }
        },
        notifications: {
            empty: 'No tienes notificaciones en este momento.'
        },
        telemetry: {
            title: 'Dispositivos',
            viewFullLogs: 'Ver Historial Completo',
            labels: {
                name: 'Nombre del Dispositivo',
                status: 'Estado',
                battery: 'Batería',
                signal: 'Señal',
                temp: 'Temp',
                action: 'Acción',
                details: 'Detalles'
            },
            empty: 'No se han detectado dispositivos activos'
        },
        events: {
            title: 'Flujo de Eventos',
            live: 'En Vivo',
            empty: 'No hay eventos recientes'
        },
        analytics: {
            title: 'Reporte de Inteligencia',
            trends: 'Eventos (6h)',
            battery: 'Salud de Batería',
            eventsPerSite: 'Eventos por Sitio',
            noData: 'Datos insuficientes para análisis',
            excellent: 'Excelente',
            good: 'Buena',
            poor: 'Pobre',
            batteryLow: 'Batería Baja',
            batteryOk: 'Batería OK'
        },
        billing: {
            title: 'Facturación',
            header: 'Suscripción',
            description: 'Gestiona tu plan de seguridad y los detalles de facturación de forma segura.',
            expiration: 'Fecha de Expiración',
            nextRenewal: 'Próxima Renovación',
            noExpiration: 'Sin fecha de expiración',
            statusActive: 'Plan Activo',
            statusExpired: 'Plan Expirado',
            portal: {
                title: 'Portal de Facturación',
                description: 'Tus pagos se procesan a través de una pasarela segura. Gestiona facturas y métodos de pago.',
                button: 'Abrir Portal de Facturación'
            },
            voucher: {
                title: 'Canjear código',
                placeholder: 'CÓDIGO - XXXX - XXXX',
                button: 'Canjear y Aplicar',
                processing: 'Procesando...',
                hint: 'Introduce tu código de activación industrial de 12 caracteres.',
                success: 'Código validado y aplicado con éxito.',
                error: 'Error al validar el código.'
            },
            history: {
                title: 'Historial de Transacciones',
                lastEntries: 'Últimas 10 operaciones',
                cols: {
                    date: 'Fecha',
                    type: 'Tipo',
                    description: 'Descripción',
                    amount: 'Importe / Beneficio',
                    status: 'Estado'
                },
                types: {
                    payment: 'Pago 💳',
                    voucher: 'Canje 🎫'
                },
                download: 'Descargar Factura (PDF)',
                viewAll: 'Ver Todas las Transacciones'
            },
            footer: {
                encrypted: 'Encriptado SSL',
                rights: '© 2024 AjaxSecurFlow Industrial Security Management. Todos los derechos reservados.'
            }
        }
    }
}

export type Translations = typeof es
