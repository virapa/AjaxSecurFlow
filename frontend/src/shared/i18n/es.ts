const PLAN_TIERS = {
    free: {
        name: 'Free',
        price: '$0',
        period: '/ para siempre',
        description: 'Exploración básica para usuarios individuales.',
        recommended: '',
        features: ['Visualización de Hubs', 'Visualización de Estado de Hubs', 'Estado de Batería de Hubs']
    },
    basic: {
        name: 'Basic',
        price: '1€',
        period: '/ mes',
        description: 'Monitoreo esencial con dispositivos ilimitados.',
        recommended: '',
        features: ['Todo lo del plan Free', 'Dispositivos Ilimitados', 'Estados de dispositivos', 'Historial de Eventos', 'Estado de Batería Dispositivos']
    },
    pro: {
        name: 'Pro',
        price: '2€',
        period: '/ mes',
        description: 'Control total y automatización avanzada.',
        recommended: 'RECOMENDADO',
        features: [
            'Todo lo del plan Basic',
            'Control de Armado',
            'Modo Noche',
            'Control de Desarmado',
            'Soporte Prioritario'
        ]
    },
    premium: {
        name: 'Premium',
        price: '8€',
        period: '/ mes',
        description: 'Integración industrial y proxy total.',
        recommended: '',
        features: [
            'Todo lo del plan Pro',
            'Generic Proxy API',
            'Webhooks Avanzados',
            'Exportación de Datos'
        ]
    }
};

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
            description: 'Nuestra arquitectura de proxy está diseñada para ofrecer una capa de seguridad adicional sobre los sistemas Ajax, garantizando que el acceso a tu infraestructura esté siempre auditado y protegido.',
            items: [
                { title: 'Auditoría Corporativa Robusta', desc: 'Historial detallado y centralizado de cada acción, comando o consulta de telemetría realizada a través del gateway.' },
                { title: 'Persistencia de Identidad Ajax', desc: 'Sistema avanzado de Doble Token que permite gestionar sesiones seguras y duraderas sin exponer credenciales críticas.' },
                { title: 'Aislamiento de Infraestructura', desc: 'Tu hardware permanece invisible en la red pública gracias a nuestra capa de abstracción de seguridad industrial.' }
            ]
        },
        pricing: {
            tag: 'Planes de Precios',
            title: 'Escala tu Seguridad',
            plans: [
                { ...PLAN_TIERS.free, desc: PLAN_TIERS.free.description },
                { ...PLAN_TIERS.basic, desc: PLAN_TIERS.basic.description },
                { ...PLAN_TIERS.pro, desc: PLAN_TIERS.pro.description },
                { ...PLAN_TIERS.premium, desc: PLAN_TIERS.premium.description }
            ]
        },
        footer: {
            tagline: 'Conectando el hardware de seguridad más fiable del mundo con la infraestructura de software moderna. Proxy de grado industrial para sistemas Ajax.',
            resources: ['Documentación API', 'Estado del Sistema', 'Centro de Soporte'],
            legal: ['Política de Privacidad', 'Términos de Servicio', 'Divulgación de Seguridad'],
            copyright: '© 2026 AjaxSecurFlow. No afiliado con Ajax Systems Ltd. Todos los derechos reservados.'
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
        errorDetail: 'Verifica tus credenciales de Ajax.',
        invalidCredentials: 'usuario o contraseña incorrectos'
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
            },
            limitedFunctions: 'Funciones Limitadas'
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
            empty: 'No hay eventos recientes',
            nonProUser: 'Acceso Restringido: Permisos Insuficientes',
            nonProHint: 'Para visualizar el historial de eventos en este panel, debe tener privilegios de ADMINISTRADOR o PRO asignados a su cuenta dentro de la aplicación oficial AJAX SECURITY (Ajustes del Hub > Usuarios).'
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
                placeholder: 'Introduce tu código de activación',
                button: 'Canjear y Aplicar',
                processing: 'Procesando...',
                hint: 'Introduce el código proporcionado.',
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
            tiers: {
                free: {
                    name: PLAN_TIERS.free.name,
                    description: PLAN_TIERS.free.description,
                    features: PLAN_TIERS.free.features
                },
                basic: {
                    name: PLAN_TIERS.basic.name,
                    description: PLAN_TIERS.basic.description,
                    features: PLAN_TIERS.basic.features
                },
                pro: {
                    name: PLAN_TIERS.pro.name,
                    description: PLAN_TIERS.pro.description,
                    features: PLAN_TIERS.pro.features
                },
                premium: {
                    name: PLAN_TIERS.premium.name,
                    description: PLAN_TIERS.premium.description,
                    features: PLAN_TIERS.premium.features
                },
                subscribe: 'Suscribirse',
                current: 'Plan Actual'
            },
            footer: {
                encrypted: 'Encriptado SSL',
                rights: '© 2026 AjaxSecurFlow. Todos los derechos reservados.'
            }
        }
    },
    support: {
        title: 'Soporte Técnico',
        description: '¿Tienes alguna duda, has encontrado un bug o necesitas ayuda? Envíanos un mensaje y nuestro equipo te responderá lo antes posible.',
        form: {
            subject: 'Asunto de la consulta',
            category: 'Categoría',
            message: 'Tu mensaje',
            emailConfirmation: 'Enviarme una copia por correo',
            submit: 'Enviar consulta',
            sending: 'Enviando...',
            success: 'Consulta enviada correctamente. Revisa tu correo para la confirmación.',
            error: 'No se pudo enviar la consulta. Por favor, inténtalo de nuevo.',
            categories: {
                bug: 'Reportar un Error (Bug)',
                question: 'Duda General',
                feedback: 'Sugerencia / Feedback',
                other: 'Otro'
            }
        }
    },
    logEvents: {
        Arm: 'Sistema Armado',
        Disarm: 'Sistema Desarmado',
        NightModeOn: 'Modo Noche Activado',
        NightModeOff: 'Modo Noche Desactivado',
        Motion: 'Movimiento Detectado',
        Fire: 'Alarma de Incendio',
        Leak: 'Inundación Detectada',
        Panic: 'Botón de Pánico',
        TamperOpen: 'Carcasa Abierta (Tamper)',
        TamperClosed: 'Carcasa Cerrada',
        Loss: 'Pérdida de Conexión',
        Restored: 'Conexión Restaurada',
        Dureza: 'Coacción Desactivada'
    },
    legal: {
        privacy: {
            title: 'Política de Privacidad',
            lastUpdated: 'Última actualización: 19 de Febrero, 2026',
            introduction: 'En AjaxSecurFlow, la privacidad y la seguridad de tu infraestructura industrial son nuestra máxima prioridad. Esta política detalla cómo gestionamos la información técnica necesaria para operar nuestro gateway y cómo protegemos la integridad de tus datos de seguridad.',
            sections: [
                { title: '1. Tratamiento de Datos de Identidad y Dual Token', content: 'Nuestra arquitectura está diseñada para minimizar el contacto con tus credenciales. Utilizamos un sistema de Dual Token cifrado: el token de acceso oficial de Ajax nunca se almacena en texto plano en nuestra base de datos. Solo almacenamos los tokens de sesión necesarios para mantener la persistencia funcional, garantizando que el acceso a la nube de Ajax sea siempre legítimo y seguro.' },
                { title: '2. Telemetría Transient vs. Auditoría Persistente', content: 'Diferenciamos entre dos tipos de datos: la telemetría en tiempo real (estado de sensores, temperatura, señal) es transitoria y solo se procesa para su visualización inmediata. Sin embargo, las acciones críticas y los cambios de estado (armado, desarmado, alarmas) se registran en nuestra infraestructura de Auditoría Corporativa para proporcionar un rastro de cumplimiento inmutable para tu organización.' },
                { title: '3. Integraciones con Terceros (Ajax y Stripe)', content: 'AjaxSecurFlow interactúa estrictamente con dos entidades externas: Ajax Systems Ltd, para la sincronización de hardware mediante su API oficial, y Stripe Inc, para la gestión segura de suscripciones y facturación. Tus datos financieros nunca tocan nuestros servidores; son procesados íntegramente por la infraestructura de Stripe, certificada con el nivel más alto de seguridad bancaria.' },
                { title: '4. Almacenamiento y Jurisdicción', content: 'Toda nuestra infraestructura tecnológica está desplegada en centros de datos ubicados en el Espacio Económico Europeo (EEE), cumpliendo rigurosamente con el Reglamento General de Protección de Datos (GDPR). Implementamos aislamiento de datos a nivel de base de datos para asegurar que la información de una organización sea técnica e lógicamente inaccesible para otras.' },
                { title: '5. Tus Derechos y Control', content: 'Como usuario de AjaxSecurFlow, mantienes el control total sobre tus datos. Puedes solicitar la exportación de tus logs de auditoría en cualquier momento (según tu plan) o la eliminación total de tu historial y tokens de persistencia. La desconexión de tu cuenta Ajax del gateway borra de forma irreversible todos los secretos criptográficos asociados a tu sesión.' }
            ]
        },
        terms: {
            title: 'Términos de Servicio',
            lastUpdated: 'Última actualización: 19 de Febrero, 2026',
            sections: [
                { title: '1. Alcance y Naturaleza del Servicio', content: 'AjaxSecurFlow proporciona una plataforma SaaS que actúa como gateway y proxy industrial para sistemas de seguridad Ajax. Este servicio es independiente y no está afiliado, patrocinado ni aprobado por Ajax Systems Ltd. El uso de este gateway requiere un equipo Ajax compatible y una cuenta activa en su ecosistema oficial.' },
                { title: '2. Modelos de Suscripción y Facturación', content: 'El acceso a las funcionalidades avanzadas (Telemetría, Comandos, Proxy API) se rige por planes de suscripción. Las suscripciones se renuevan automáticamente al final de cada periodo de facturación a través de Stripe. El usuario puede cancelar la renovación en cualquier momento desde el panel de facturación, manteniendo el acceso hasta el final del ciclo pagado.' },
                { title: '3. Uso Profesional y Prohibiciones', content: 'El servicio está diseñado para uso profesional e industrial. Queda terminantemente prohibido el uso del gateway para realizar ataques de denegación de servicio (DoS), ingeniería inversa del proxy, o cualquier actividad que pueda degradar la estabilidad de la plataforma para otros usuarios. El incumplimiento de estas normas resultará en la suspensión inmediata de la cuenta sin derecho a reembolso.' },
                { title: '4. Compromiso de Disponibilidad (SLA)', content: 'Nos esforzamos por mantener una disponibilidad (uptime) del 99.9%. Las ventanas de mantenimiento programado se comunicarán con antelación y se realizarán preferentemente en horarios de baja actividad para minimizar el impacto. AjaxSecurFlow no se responsabiliza de interrupciones causadas por fallos en los servidores de Ajax Systems o problemas de conectividad local del hardware del usuario.' },
                { title: '5. Propiedad Intelectual y Limitaciones', content: 'Todo el software, diseños y algoritmos propios del gateway AjaxSecurFlow son propiedad exclusiva de sus desarrolladores. El usuario es responsable de asegurar que el uso de este gateway cumple con las políticas locales de seguridad privada y normativas vigentes en su jurisdicción geográfica.' },
                { title: '6. Modificaciones de las Condiciones', content: 'Nos reservamos el derecho de actualizar estos términos para reflejar cambios tecnológicos o regulatorios. El uso continuado del servicio tras un cambio en los términos implica la aceptación de las nuevas condiciones.' }
            ]
        },
        security: {
            title: 'Divulgación de Seguridad',
            lastUpdated: 'Última actualización: 19 de Febrero, 2026',
            introduction: 'Nuestra arquitectura se basa en el principio de "Seguridad por Diseño". Implementamos múltiples capas de protección para asegurar que cada bit que pasa por el proxy sea gestionado con integridad.',
            contact: 'Si crees haber encontrado una vulnerabilidad, por favor contáctanos de forma responsable en: security@ajaxsecurflow.com',
            measures: [
                'Arquitectura de sesiones aisladas (Session Isolation).',
                'Validación estricta de esquemas en todas las peticiones proxy.',
                'Rotación automática de claves de infraestructura cada 24 horas.',
                'Protección de fuerza bruta y limitación de tasa (Rate Limiting) industrial.'
            ]
        }
    }
}

export type Translations = typeof es
