import React, { createContext, useState, useContext, useEffect } from 'react';

// Language Context
const LanguageContext = createContext();

// Custom hook to use language context
export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

// Detect browser language
const detectBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.languages[0];
  if (browserLang.startsWith('it')) {
    return 'it';
  }
  return 'en'; // Default to English
};

// Language Provider Component
export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    // Check localStorage first, then browser detection
    const savedLanguage = localStorage.getItem('kinaura_language');
    if (savedLanguage) {
      return savedLanguage;
    }
    return detectBrowserLanguage();
  });

  // Update localStorage when language changes
  useEffect(() => {
    localStorage.setItem('kinaura_language', language);
  }, [language]);

  const switchLanguage = (lang) => {
    setLanguage(lang);
  };

  const value = {
    language,
    switchLanguage,
    isItalian: language === 'it',
    isEnglish: language === 'en'
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

// Translation hook
export const useTranslation = () => {
  const { language } = useLanguage();

  const t = (key, params = {}) => {
    const translation = translations[language] || translations.en;
    let text = getNestedValue(translation, key) || getNestedValue(translations.en, key) || key;
    
    // Replace parameters in translation
    Object.keys(params).forEach(param => {
      text = text.replace(`{{${param}}}`, params[param]);
    });
    
    return text;
  };

  return { t };
};

// Helper function to get nested object values
const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, key) => current?.[key], obj);
};

// Comprehensive translations for patient-facing sections
const translations = {
  en: {
    // Navigation & Header
    nav: {
      dashboard: "Dashboard",
      services: "Services", 
      appointments: "My Bookings",
      resources: "Resources",
      concierge: "KinAura Concierge",
      profile: "Profile",
      logout: "Logout",
      login: "Login",
      menu: "Menu"
    },

    // Dashboard
    dashboard: {
      welcome: "Welcome back",
      welcomeMessage: "Your personalized wellness journey continues",
      yourWellnessTools: "Your Wellness Tools",
      recentActivity: "Recent Activity",
      upcomingAppointments: "Upcoming Appointments",
      noUpcomingAppointments: "No upcoming appointments",
      viewAllAppointments: "View All Appointments",
      bookConsultation: "Book Consultation",
      
      // Wellness Tools
      tools: {
        longevityScoreboard: "Longevity Scoreboard",
        questionnaires: "Questionnaires", 
        healthDashboard: "Health Dashboard",
        concierge: "KinAura Concierge",
        resources: "Resources",
        serviceGroups: "Service Groups",
        personalizedProtocol: "Personalized Protocol",
        appointments: "Appointments"
      }
    },

    // Personalized Protocol
    protocol: {
      title: "Join the KinAura Revolution",
      subtitle: "Experience the future of personalized medicine with our proprietary AI-powered protocol engine that analyzes your unique genomic, blood, and microbiome data to create scientifically-validated treatment protocols in under one second.",
      europeanCenter: "Europe's First AI-Powered Precision Medicine Center",
      uniqueCenter: "KinAura is the unique European center offering proprietary AI technology with Harvard Medical School validation for personalized protocol development",
      multiOmicsTitle: "Multi-Omics Analysis: The Foundation of Precision Medicine",
      
      genomics: {
        title: "Genomic Intelligence",
        description: "Advanced genetic profiling reveals mutations like MTHFR, COMT, and VDR variants that influence treatment response, metabolic pathways, and therapeutic safety profiles for unprecedented personalization."
      },
      biomarkers: {
        title: "47+ Biomarker Analysis", 
        description: "Comprehensive blood analysis measuring CRP, HbA1c, ATP index, hormonal panels, and inflammatory markers to create your unique biological fingerprint for AI-powered cluster assignment."
      },
      microbiome: {
        title: "Microbiome Mapping",
        description: "Advanced gut ecosystem analysis examining Firmicutes/Bacteroidetes ratios, zonulina levels, and SIBO markers to optimize treatment absorption and reduce systemic inflammation."
      },
      
      aiEngine: "Proprietary AI Protocol Engine",
      aiDescription: "Our breakthrough AI system processes over 2 million medical studies in real-time, utilizing K-means clustering across 23 patient cohorts, Bayesian dose optimization, and reinforcement learning to generate personalized protocols with 94.2% accuracy.",
      
      treatmentTitle: "Advanced Treatment Integration",
      precisionDosing: {
        title: "Precision Dosing",
        description: "Bayesian algorithms calculate optimal dosages for NAD+, GLP-1, IV therapies, and peptides based on your age, weight, metabolic markers, and genetic variants."
      },
      treatmentSequencing: {
        title: "Treatment Sequencing", 
        description: "Deep Q-Learning algorithms optimize treatment timing and combinations across 50+ therapeutic modalities including Red Light Therapy, EBOO, and regenerative aesthetics."
      },
      
      ctaTitle: "Ready to Experience Precision Medicine?",
      ctaSubtitle: "Join the select group of individuals experiencing the future of personalized wellness today. Discover your unique protocol based on comprehensive DNA, blood, and microbiome analysis.",
      beginAssessment: "Begin Your Personalized Assessment",
      comprehensiveAnalysis: "Comprehensive multi-omics analysis and AI protocol generation",
      
      modalTitle: "Welcome to Precision Medicine",
      modalMessage: "Thank you for your interest in our AI-powered personalized protocol program. Our team will contact you within 24 hours to begin your comprehensive multi-omics assessment.",
      scheduleConsultation: "Schedule Consultation",
      close: "Close",
      backToDashboard: "Back to Dashboard"
    },

    // Chatbot/Concierge
    chatbot: {
      title: "KinAura Concierge",
      subtitle: "Your AI-powered wellness companion",
      placeholder: "Ask me anything about treatments, wellness, or book an appointment...",
      send: "Send",
      typing: "KinAura Concierge is typing...",
      welcomeMessage: "Hello! I'm your KinAura Concierge. How can I assist you with your wellness journey today?",
      suggestedQuestions: "Suggested Questions",
      clearChat: "Clear Chat",
      minimize: "Minimize",
      maximize: "Maximize"
    },

    // Services
    services: {
      title: "Our Services",
      subtitle: "Discover our comprehensive wellness and aesthetic treatments",
      bookNow: "Book Now",
      learnMore: "Learn More",
      duration: "Duration",
      price: "Price",
      category: "Category",
      benefits: "Benefits",
      suitableFor: "Suitable For"
    },

    // Appointments/Bookings
    bookings: {
      title: "My Bookings",
      subtitle: "Manage your appointments and treatment history",
      upcoming: "Upcoming Appointments",
      past: "Past Appointments", 
      cancelled: "Cancelled Appointments",
      noAppointments: "No appointments found",
      bookNew: "Book New Appointment",
      cancel: "Cancel",
      reschedule: "Reschedule",
      confirmed: "Confirmed",
      pending: "Pending",
      cancelled: "Cancelled",
      completed: "Completed",
      date: "Date",
      time: "Time",
      treatment: "Treatment",
      status: "Status",
      notes: "Notes"
    },

    // Appointment Booking Flow
    booking: {
      title: "Book Appointment",
      selectService: "Select Service",
      selectDate: "Select Date",
      selectTime: "Select Time",
      personalInfo: "Personal Information",
      confirmation: "Confirmation",
      bookingSuccess: "Booking Successful!",
      next: "Next",
      back: "Back",
      confirm: "Confirm Booking",
      fullName: "Full Name",
      email: "Email",
      phone: "Phone Number",
      notes: "Additional Notes",
      bookingDetails: "Booking Details",
      totalPrice: "Total Price"
    },

    // General UI Elements
    ui: {
      loading: "Loading...",
      error: "An error occurred",
      tryAgain: "Try Again",
      success: "Success",
      save: "Save",
      cancel: "Cancel",
      edit: "Edit",
      delete: "Delete",
      view: "View",
      download: "Download",
      upload: "Upload",
      search: "Search",
      filter: "Filter",
      sort: "Sort",
      clear: "Clear",
      apply: "Apply",
      reset: "Reset",
      continue: "Continue",
      finish: "Finish",
      previous: "Previous",
      next: "Next"
    },

    // Time & Date
    time: {
      morning: "Morning",
      afternoon: "Afternoon", 
      evening: "Evening",
      today: "Today",
      tomorrow: "Tomorrow",
      thisWeek: "This Week",
      nextWeek: "Next Week",
      monday: "Monday",
      tuesday: "Tuesday", 
      wednesday: "Wednesday",
      thursday: "Thursday",
      friday: "Friday",
      saturday: "Saturday",
      sunday: "Sunday"
    }
  },

  it: {
    // Navigation & Header
    nav: {
      dashboard: "Dashboard",
      services: "Servizi",
      appointments: "Le Mie Prenotazioni", 
      resources: "Risorse",
      concierge: "KinAura Concierge",
      profile: "Profilo",
      logout: "Esci",
      login: "Accedi",
      menu: "Menu"
    },

    // Dashboard  
    dashboard: {
      welcome: "Bentornato",
      welcomeMessage: "Il tuo viaggio personalizzato verso il benessere continua",
      yourWellnessTools: "I Tuoi Strumenti per il Benessere", 
      recentActivity: "Attività Recente",
      upcomingAppointments: "Prossimi Appuntamenti",
      noUpcomingAppointments: "Nessun appuntamento in programma",
      viewAllAppointments: "Visualizza Tutti gli Appuntamenti",
      bookConsultation: "Prenota Consulenza",
      
      // Wellness Tools
      tools: {
        longevityScoreboard: "Longevity Scoreboard",
        questionnaires: "Questionari",
        healthDashboard: "Dashboard Salute", 
        concierge: "KinAura Concierge",
        resources: "Risorse",
        serviceGroups: "Gruppi di Servizi",
        personalizedProtocol: "Protocollo Personalizzato",
        appointments: "Appuntamenti"
      }
    },

    // Personalized Protocol
    protocol: {
      title: "Unisciti alla Rivoluzione KinAura",
      subtitle: "Vivi il futuro della medicina personalizzata con il nostro motore di protocolli AI proprietario che analizza i tuoi dati genomici, ematici e del microbioma unici per creare protocolli terapeutici scientificamente validati in meno di un secondo.",
      europeanCenter: "Il Primo Centro Europeo di Medicina di Precisione Alimentato da AI",
      uniqueCenter: "KinAura è l'unico centro europeo che offre tecnologia AI proprietaria con validazione Harvard Medical School per lo sviluppo di protocolli personalizzati",
      multiOmicsTitle: "Analisi Multi-Omica: Le Fondamenta della Medicina di Precisione",
      
      genomics: {
        title: "Intelligenza Genomica",
        description: "Il profiling genetico avanzato rivela mutazioni come le varianti MTHFR, COMT e VDR che influenzano la risposta al trattamento, le vie metaboliche e i profili di sicurezza terapeutica per una personalizzazione senza precedenti."
      },
      biomarkers: {
        title: "Analisi di 47+ Biomarcatori",
        description: "Analisi ematica completa che misura CRP, HbA1c, indice ATP, pannelli ormonali e marcatori infiammatori per creare la tua impronta biologica unica per l'assegnazione cluster alimentata da AI."
      },
      microbiome: {
        title: "Mappatura del Microbioma",
        description: "Analisi avanzata dell'ecosistema intestinale che esamina i rapporti Firmicutes/Bacteroidetes, i livelli di zonulina e i marcatori SIBO per ottimizzare l'assorbimento del trattamento e ridurre l'infiammazione sistemica."
      },
      
      aiEngine: "Motore di Protocolli AI Proprietario",
      aiDescription: "Il nostro rivoluzionario sistema AI elabora oltre 2 milioni di studi medici in tempo reale, utilizzando clustering K-means su 23 coorti di pazienti, ottimizzazione della dose bayesiana e reinforcement learning per generare protocolli personalizzati con il 94,2% di accuratezza.",
      
      treatmentTitle: "Integrazione Avanzata dei Trattamenti",
      precisionDosing: {
        title: "Dosaggio di Precisione", 
        description: "Gli algoritmi bayesiani calcolano dosaggi ottimali per NAD+, GLP-1, terapie IV e peptidi basati su età, peso, marcatori metabolici e varianti genetiche."
      },
      treatmentSequencing: {
        title: "Sequenziamento dei Trattamenti",
        description: "Gli algoritmi Deep Q-Learning ottimizzano i tempi e le combinazioni di trattamento su oltre 50 modalità terapeutiche incluse Red Light Therapy, EBOO ed estetica rigenerativa."
      },
      
      ctaTitle: "Pronto per Sperimentare la Medicina di Precisione?",
      ctaSubtitle: "Unisciti al gruppo selezionato di individui che sperimentano oggi il futuro del benessere personalizzato. Scopri il tuo protocollo unico basato su analisi complete di DNA, sangue e microbioma.",
      beginAssessment: "Inizia la Tua Valutazione Personalizzata",
      comprehensiveAnalysis: "Analisi multi-omica completa e generazione di protocolli AI",
      
      modalTitle: "Benvenuto nella Medicina di Precisione",
      modalMessage: "Grazie per il tuo interesse nel nostro programma di protocolli personalizzati alimentato da AI. Il nostro team ti contatterà entro 24 ore per iniziare la tua valutazione multi-omica completa.",
      scheduleConsultation: "Prenota Consulenza",
      close: "Chiudi",
      backToDashboard: "Torna al Dashboard"
    },

    // Chatbot/Concierge
    chatbot: {
      title: "KinAura Concierge",
      subtitle: "Il tuo compagno di benessere alimentato da AI",
      placeholder: "Chiedimi qualsiasi cosa sui trattamenti, benessere o prenota un appuntamento...",
      send: "Invia",
      typing: "KinAura Concierge sta scrivendo...",
      welcomeMessage: "Ciao! Sono il tuo KinAura Concierge. Come posso assisterti nel tuo viaggio verso il benessere oggi?",
      suggestedQuestions: "Domande Suggerite",
      clearChat: "Cancella Chat",
      minimize: "Riduci a icona",
      maximize: "Ingrandisci"
    },

    // Services
    services: {
      title: "I Nostri Servizi",
      subtitle: "Scopri i nostri trattamenti completi per benessere ed estetica",
      bookNow: "Prenota Ora",
      learnMore: "Scopri di Più",
      duration: "Durata",
      price: "Prezzo",
      category: "Categoria",
      benefits: "Benefici", 
      suitableFor: "Adatto Per"
    },

    // Appointments/Bookings
    bookings: {
      title: "Le Mie Prenotazioni",
      subtitle: "Gestisci i tuoi appuntamenti e la cronologia dei trattamenti",
      upcoming: "Appuntamenti in Arrivo",
      past: "Appuntamenti Passati",
      cancelled: "Appuntamenti Annullati", 
      noAppointments: "Nessun appuntamento trovato",
      bookNew: "Prenota Nuovo Appuntamento",
      cancel: "Annulla",
      reschedule: "Riprogramma",
      confirmed: "Confermato",
      pending: "In Attesa",
      cancelled: "Annullato",
      completed: "Completato",
      date: "Data",
      time: "Ora",
      treatment: "Trattamento",
      status: "Stato",
      notes: "Note"
    },

    // Appointment Booking Flow
    booking: {
      title: "Prenota Appuntamento",
      selectService: "Seleziona Servizio",
      selectDate: "Seleziona Data",
      selectTime: "Seleziona Ora", 
      personalInfo: "Informazioni Personali",
      confirmation: "Conferma",
      bookingSuccess: "Prenotazione Riuscita!",
      next: "Avanti",
      back: "Indietro",
      confirm: "Conferma Prenotazione", 
      fullName: "Nome Completo",
      email: "Email",
      phone: "Numero di Telefono",
      notes: "Note Aggiuntive",
      bookingDetails: "Dettagli Prenotazione",
      totalPrice: "Prezzo Totale"
    },

    // General UI Elements
    ui: {
      loading: "Caricamento...",
      error: "Si è verificato un errore",
      tryAgain: "Riprova",
      success: "Successo", 
      save: "Salva",
      cancel: "Annulla",
      edit: "Modifica",
      delete: "Elimina",
      view: "Visualizza",
      download: "Scarica",
      upload: "Carica",
      search: "Cerca",
      filter: "Filtra", 
      sort: "Ordina",
      clear: "Cancella",
      apply: "Applica",
      reset: "Reimposta",
      continue: "Continua",
      finish: "Termina",
      previous: "Precedente",
      next: "Prossimo"
    },

    // Time & Date
    time: {
      morning: "Mattina",
      afternoon: "Pomeriggio",
      evening: "Sera",
      today: "Oggi", 
      tomorrow: "Domani",
      thisWeek: "Questa Settimana",
      nextWeek: "Prossima Settimana",
      monday: "Lunedì",
      tuesday: "Martedì",
      wednesday: "Mercoledì", 
      thursday: "Giovedì",
      friday: "Venerdì",
      saturday: "Sabato",
      sunday: "Domenica"
    }
  }
};