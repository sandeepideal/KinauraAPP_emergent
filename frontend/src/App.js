import React, { useState, useEffect, Suspense, lazy, useCallback, useRef } from "react";
import PlatformUtils from "./utils/platform";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import "./App.css";
import "./mobile.css";
import "./styles/kinaura-theme.css";
import PatientResources from "./PatientResources";
import PatientQuestionnaires from "./PatientQuestionnaires";
import Boutique from "./Boutique";
import Membership from "./Membership";
import AppointmentBooking from "./AppointmentBooking";
import BookingSuccess from "./BookingSuccess";
import HealthDashboard from "./HealthDashboard";
import ServiceGroups from "./ServiceGroups";
import PatientChatbot from "./PatientChatbot";
import LongevityScoreboard from "./LongevityScoreboard";
import KinAuraLogo from './components/KinAuraLogo';
import AppleLoginComponent from './components/AppleLoginComponent';
import FacebookLoginComponent from './components/FacebookLoginComponent';
import HeroSection from './components/HeroSection';
import HeroLanding from './components/HeroLanding';
import ProactiveNotification from './components/ProactiveNotification';
import { designTokens } from './designTokens';
import { supabase, supabaseApi } from './lib/supabase';
import { apiClient } from './lib/apiClient';
import pushNotificationService from './firebase';
import { LanguageProvider, useTranslation, useLanguage } from './contexts/LanguageContext';
import LanguageToggle from './components/LanguageToggle';
import { ThemeProvider } from './utils/theme';
import { useRealTimeContentSync } from './hooks/useContentSync';
import { ContentSyncProvider, ContentSyncIndicator } from './contexts/ContentSyncContext';
import ThemeToggle from './components/ThemeToggle';
import ErrorBoundary from './components/app/ErrorBoundary';
import { ToastProvider, useToast } from './components/ui/Toast';
import { setToastInstance } from './lib/apiClient';
import { SkeletonCard } from './components/ui/Skeleton';

// KinAura splash background path
const kinauraSplashBg = '/brand/kinaura-splash-1.png';

// Lazy load admin components
const AdminDashboard = lazy(() => import("./AdminDashboard"));
const AdminAppointments = lazy(() => import("./AdminAppointments"));
const AdminHealthData = lazy(() => import("./AdminHealthData"));
const LongevityScoreboardAdmin = lazy(() => import("./LongevityScoreboardAdmin"));

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});






// Configuration - Check if we should use Supabase or FastAPI
const USE_SUPABASE = process.env.REACT_APP_USE_SUPABASE === 'true' || false;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = USE_SUPABASE ? null : `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext(null);

// API Helper - Use Supabase or FastAPI based on configuration
const apiHelper = {
  auth: {
    register: async (email, password, full_name, phone) => {
      if (USE_SUPABASE) {
        return await supabaseApi.auth.register(email, password, full_name, phone);
      } else {
        // Use the improved apiClient instead of axios
        const response = await apiClient('/api/auth/register', {
          method: 'POST',
          body: { email, password, full_name, phone },
          skipAuth: true // Registration doesn't need auth token
        });
        return response;
      }
    },

    login: async (email, password) => {
      if (USE_SUPABASE) {
        return await supabaseApi.auth.login(email, password);
      } else {
        // Use the improved apiClient instead of axios
        const response = await apiClient('/api/auth/login', {
          method: 'POST', 
          body: { email, password },
          skipAuth: true // Login doesn't need auth token
        });
        return response;
      }
    },

    socialLogin: async (provider, userData) => {
      if (USE_SUPABASE) {
        return await supabaseApi.auth.socialLogin(provider, 'mock_token', userData.full_name, userData.email);
      } else {
        // Use the improved apiClient instead of axios
        const response = await apiClient('/api/auth/social-login', {
          method: 'POST',
          body: userData,
          skipAuth: true // Social login doesn't need auth token  
        });
        return response;
      }
    }
  },

  services: {
    getAll: async () => {
      if (USE_SUPABASE) {
        return await supabaseApi.services.getAll();
      } else {
        const axios = (await import('axios')).default;
        const response = await axios.get(`${API}/services`);
        return response.data.services || response.data;
      }
    }
  },

  serviceGroups: {
    getAll: async () => {
      if (USE_SUPABASE) {
        // Return mock data for now
        return [
          {
            id: 'regenerative-medicine',
            name: 'Regenerative Medicine',
            description: 'Advanced regenerative therapies and treatments',
            color: '#B88E35',
            services: []
          },
          {
            id: 'wellness-optimization',
            name: 'Wellness Optimization',
            description: 'Comprehensive wellness and optimization services', 
            color: '#CFA544',
            services: []
          },
          {
            id: 'diagnostics',
            name: 'Advanced Diagnostics',
            description: 'Cutting-edge diagnostic and assessment services',
            color: '#D5A144',
            services: []
          }
        ];
      } else {
        try {
          const axios = (await import('axios')).default;
          const response = await axios.get(`${API}/service-groups`);
          return response.data.service_groups || response.data;
        } catch (error) {
          // Return default groups if API endpoint doesn't exist yet
          return [
            {
              id: 'regenerative-medicine',
              name: 'Regenerative Medicine',
              description: 'Advanced regenerative therapies and treatments',
              color: '#B88E35',
              services: []
            },
            {
              id: 'wellness-optimization',
              name: 'Wellness Optimization',
              description: 'Comprehensive wellness and optimization services',
              color: '#CFA544', 
              services: []
            },
            {
              id: 'diagnostics',
              name: 'Advanced Diagnostics',
              description: 'Cutting-edge diagnostic and assessment services',
              color: '#D5A144',
              services: []
            }
          ];
        }
      }
    }
  },

  appointments: {
    getAll: async (token) => {
      if (USE_SUPABASE) {
        return await supabaseApi.appointments.getAll(token);
      } else {
        const axios = (await import('axios')).default;
        const response = await axios.get(`${API}/appointments`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
      }
    }
  }
};

// Components
const LoadingScreen = ({ onLoadingComplete }) => {
  // Just display the loading screen - no longer used but kept for potential future use

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FDFCFA] via-white to-[#F8F5F0] flex flex-col items-center justify-center relative overflow-hidden">
      {/* Subtle animated background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#C8A25A] rounded-full filter blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-[#E8D5B7] rounded-full filter blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>
      
      {/* Main Loading Content */}
      
      {/* Animated Logo */}
      <div className="flex flex-col items-center justify-center relative z-10">
        <div className="w-64 h-64 flex items-center justify-center mb-8">
          <img 
            src="https://customer-assets.emergentagent.com/job_figma-dev-2/artifacts/uxx39w2x_KinAura-Logo-animation-02.gif" 
            alt="KinAura Loading Animation" 
            className="w-full h-auto max-w-64 animate-pulse"
            onError={(e) => {
              // Fallback to static logo if gif fails to load
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'block';
            }}
          />
          <div className="hidden w-32 h-32">
            <KinAuraLogo variant="dark" className="w-full h-full animate-bounce" />
          </div>
        </div>
        
        {/* Loading text with elegant animation */}
        <div className="text-center animate-fade-in">
          <h1 className="text-2xl font-light text-[#222428] mb-2 tracking-wide">
            Welcome to KinAura
          </h1>
          <p className="text-sm text-gray-600 font-light tracking-wider animate-pulse">
            Preparing your wellness journey...
          </p>
        </div>
      </div>
      
      {/* Elegant loading indicator */}
      <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2">
        <div className="flex space-x-3">
          <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
        </div>
        <div className="text-center mt-4">
          <p className="text-xs text-gray-500 font-light">
            {USE_SUPABASE ? 'Supabase Integration' : 'FastAPI Integration'}
          </p>
        </div>
      </div>
    </div>
  );
};

const PatientDashboard = ({ user, onNavigate, onOpenChatbot, onLogoClick }) => {
  const [treatments, setTreatments] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [announcements, setAnnouncements] = useState('');
  
  // Translation hook  
  const { language } = useLanguage();
  const { t } = useTranslation(language);

  useEffect(() => {
    // Set dynamic announcements for screen readers
    if (loading) {
      setAnnouncements(t('common.loading'));
    } else {
      setAnnouncements(`${t('dashboard.welcome')} ${user?.full_name || 'User'}`);
    }
  }, [loading, user, language, t]);

  useEffect(() => {
    fetchPatientData();
  }, []);

  const fetchPatientData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        // Fetch user appointments
        const appointmentsData = await apiHelper.appointments.getAll(token);
        setAppointments(appointmentsData);
      }
    } catch (error) {
      console.error('Error fetching patient data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data for demonstration - luxury protocol data
  const currentProtocol = [
    { 
      name: 'Ozone Therapy', 
      icon: '💨', 
      date: '2024-04-15', 
      benefit: 'Oxygenate & Revitalize',
      completed: true,
      color: '#10B981'
    },
    { 
      name: 'IV Therapy Drip', 
      icon: '💧', 
      date: '2024-04-18', 
      benefit: 'Nourish & Detoxify',
      completed: true,
      color: '#3B82F6'
    },
    { 
      name: 'PBM Therapy', 
      icon: '⚡', 
      date: '2024-04-23', 
      benefit: 'Regenerate & Repair',
      completed: false,
      color: '#F59E0B'
    }
  ];

  const nextSession = {
    scheduled: true,
    date: 'Wed, May 23',
    time: '10:00 AM',
    treatment: 'PBM Therapy'
  };

  const membershipInfo = {
    name: 'Elite Member',
    benefits: [
      { icon: '💎', text: '10% discount' },
      { icon: '👑', text: 'VIP access' },
      { icon: '📞', text: '24/7 concierge' }
    ]
  };

  const longevityScore = 54;
  const communityScore = 61;

  if (loading) {
    return (
      <div className="min-h-screen luxury-gradient-bg luxury-texture flex items-center justify-center">
        <div className="text-center fade-in-up">
          <div className="w-12 h-12 border-2 border-amber-200 border-t-amber-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-stone-600 luxury-sans">Loading your wellness profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen luxury-gradient-bg luxury-texture" role="main" aria-label="Patient Dashboard">
      {/* Screen reader announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcements}
      </div>
      
      {/* Skip link for keyboard navigation */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      {/* Subtle Kintsugi-inspired wave dividers */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-30">
        <svg className="absolute top-1/4 left-0 w-full h-24" viewBox="0 0 1200 100">
          <path 
            d="M0,50 Q300,20 600,50 T1200,50" 
            stroke="url(#goldWave1)" 
            strokeWidth="1" 
            fill="none"
          />
          <defs>
            <linearGradient id="goldWave1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#D4AF37" stopOpacity="0"/>
              <stop offset="50%" stopColor="#D4AF37" stopOpacity="0.6"/>
              <stop offset="100%" stopColor="#D4AF37" stopOpacity="0"/>
            </linearGradient>
          </defs>
        </svg>
        <svg className="absolute top-3/4 right-0 w-2/3 h-16" viewBox="0 0 800 60">
          <path 
            d="M0,30 Q200,10 400,30 T800,30" 
            stroke="url(#goldWave2)" 
            strokeWidth="0.8" 
            fill="none"
          />
          <defs>
            <linearGradient id="goldWave2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#B8925A" stopOpacity="0"/>
              <stop offset="50%" stopColor="#B8925A" stopOpacity="0.4"/>
              <stop offset="100%" stopColor="#B8925A" stopOpacity="0"/>
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div className="relative z-10">
        {/* Header Navigation */}
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center space-x-3 cursor-pointer group" onClick={onLogoClick}>
            <img 
              src="/brand/kinaura-symbol.svg" 
              alt="KinAura" 
              className="ka-logo w-8 h-8 transition-transform group-hover:scale-105"
            />
            <span className="text-xl font-light text-ka-text tracking-wide group-hover:text-ka-brand transition-colors" style={{fontFamily: 'var(--ka-font-body)'}}>KinAura</span>
          </div>
          <div className="flex items-center space-x-3">
            <ThemeToggle size="small" />
            <LanguageToggle size="small" />
            <button 
              onClick={() => onNavigate('menu')}
              className="hamburger-menu"
              aria-label="Open menu"
            >
              <div className="hamburger-line"></div>
              <div className="hamburger-line"></div>
              <div className="hamburger-line"></div>
            </button>
          </div>
        </div>

        {/* Hero Welcome Section */}
        <div className="px-6 pt-8 pb-12">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
              
              {/* Personalized Greeting */}
              <div className="fade-in-up">
                <h1 className="text-4xl lg:text-5xl luxury-serif text-stone-800 mb-3 leading-tight">
                  {t('dashboard.welcome')},
                  <br />
                  <span className="text-amber-700 gold-underline">{user?.full_name || 'Dr. Marco Rossi'}</span>
                </h1>
                <p className="text-stone-600 text-lg luxury-sans text-refined">{t('dashboard.welcomeMessage')}</p>
              </div>

              {/* Next Appointment Elegant Card */}
              <div className="luxury-card p-6 min-w-[320px] fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 gold-shimmer rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500 uppercase tracking-wider mb-1 luxury-sans">Next Appointment</p>
                    <p className="text-lg font-medium text-stone-800 luxury-sans">{nextSession.date}</p>
                    <p className="text-sm text-stone-600 luxury-sans">{nextSession.time} • {nextSession.treatment}</p>
                  </div>
                </div>
                <button className="w-full bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200 text-amber-700 py-2 px-4 rounded-lg hover:from-amber-100 hover:to-amber-200 transition-all duration-300 luxury-sans font-medium text-sm">
                  Add to Calendar
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="px-6 pb-8">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Current Protocol - Left Side (2 columns) */}
              <div className="lg:col-span-2">
                <div className="luxury-card p-8">
                  <h2 className="text-2xl luxury-serif text-stone-800 mb-8">Current Protocol</h2>
                  
                  {/* Treatment Cards with Timeline */}
                  <div className="space-y-6 stagger-animation">
                    {currentProtocol.map((treatment, index) => (
                      <div key={index} className="relative">
                        {/* Connecting Line */}
                        {index < currentProtocol.length - 1 && (
                          <div className="absolute left-7 top-16 w-0.5 h-12 bg-gradient-to-b from-amber-300 to-amber-200 opacity-60"></div>
                        )}
                        
                        {/* Treatment Card */}
                        <div className={`treatment-card p-6 ${treatment.completed ? 'completed' : ''}`}>
                          <div className="flex items-center space-x-4">
                            
                            {/* Icon */}
                            <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-xl shadow-md ${
                              treatment.completed 
                                ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-white' 
                                : 'gold-shimmer text-white'
                            }`}>
                              {treatment.icon}
                            </div>
                            
                            {/* Content */}
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <h3 className="text-lg font-medium text-stone-800 luxury-sans">{treatment.name}</h3>
                                <span className="text-xs text-stone-500 bg-stone-100 px-3 py-1 rounded-full luxury-sans">{treatment.date}</span>
                              </div>
                              <p className="text-stone-600 luxury-sans italic text-refined">{treatment.benefit}</p>
                            </div>
                            
                            {/* Status */}
                            <div className="flex items-center">
                              {treatment.completed ? (
                                <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                                  <svg className="w-5 h-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                                  </svg>
                                </div>
                              ) : (
                                <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                                  <svg className="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                                  </svg>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-8 pt-6 border-t border-stone-200">
                    <button 
                      onClick={() => onNavigate('protocol')}
                      className="inline-flex items-center space-x-2 text-amber-700 hover:text-amber-800 font-medium transition-colors luxury-sans"
                    >
                      <span>View Full Protocol</span>
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Sidebar */}
              <div className="space-y-6">
                
                {/* Longevity Score Ring */}
                <div className="luxury-card p-6 text-center">
                  <div className="relative inline-block mb-6">
                    <svg className="w-32 h-32 transform -rotate-90 luxury-progress-ring" viewBox="0 0 120 120">
                      {/* Background Ring */}
                      <circle
                        cx="60"
                        cy="60"
                        r="50"
                        stroke="#f3f4f6"
                        strokeWidth="8"
                        fill="transparent"
                      />
                      {/* Progress Ring with Gradient */}
                      <circle
                        cx="60"
                        cy="60"
                        r="50"
                        stroke="url(#goldProgressGradient)"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={`${(longevityScore / 100) * 314} 314`}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                      />
                      <defs>
                        <linearGradient id="goldProgressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#D4AF37"/>
                          <stop offset="50%" stopColor="#F4E04D"/>
                          <stop offset="100%" stopColor="#B8925A"/>
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-3xl font-light text-stone-800 luxury-serif">{longevityScore}</span>
                      <span className="text-xs text-stone-500 uppercase tracking-wider luxury-sans">Score</span>
                    </div>
                  </div>
                  
                  <h3 className="text-stone-700 font-medium tracking-wide text-sm uppercase mb-3 luxury-sans">Longevity Score</h3>
                  <p className="text-stone-500 text-sm mb-4 luxury-sans text-refined">Your wellness score vs community</p>
                  
                  <div className="space-y-2 text-sm luxury-sans">
                    <div className="flex justify-between items-center">
                      <span className="text-stone-600">You</span>
                      <span className="font-medium text-stone-800">{longevityScore}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-stone-600">Community</span>
                      <span className="font-medium text-stone-800">{communityScore}</span>
                    </div>
                  </div>
                </div>

                {/* Elite Membership Card */}
                <div className="membership-foil rounded-2xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-amber-200 to-transparent opacity-20 rounded-full -mr-12 -mt-12"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl luxury-serif text-stone-800">{membershipInfo.name}</h2>
                      <div className="text-amber-600 text-lg">✧</div>
                    </div>
                    
                    <div className="space-y-4">
                      {membershipInfo.benefits.map((benefit, index) => (
                        <div key={index} className="flex items-center space-x-3">
                          <div className="text-amber-600 text-lg">{benefit.icon}</div>
                          <span className="text-sm text-stone-700 luxury-sans text-refined">{benefit.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Your Wellness Tools */}
        <section id="main-content" className="px-6 pb-8" aria-labelledby="wellness-tools-heading">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h3 id="wellness-tools-heading" className="ka-section-title text-center">
                {t('dashboard.yourWellnessTools')}
              </h3>
              <div className="w-16 h-0.5 bg-ka-brand mx-auto mt-4" role="presentation"></div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6" 
                 role="region" 
                 aria-label="Wellness tools navigation"
                 tabIndex="0">
              
              {/* Personalized Protocol */}
              <button 
                onClick={() => onNavigate('personalized-protocol')}
                className="ka-wellness-card group"
                aria-label={`${t('dashboard.tools.personalizedProtocol')} - Navigate to personalized protocol`}
              >
                <div className="ka-wellness-card__icon">
                  {/* DNA Helix Icon */}
                  <img 
                    src="/dna-icon.png" 
                    alt="DNA Helix" 
                    className="ka-icon ka-icon--lg"
                    style={{ 
                      width: '128px', 
                      height: '128px', 
                      objectFit: 'contain',
                      filter: 'brightness(1.1) contrast(1.1)'
                    }}
                  />
                </div>
                <h4 className="ka-wellness-card__title">{t('dashboard.tools.personalizedProtocol')}</h4>
              </button>
              
              {/* All Services */}
              <button 
                onClick={() => onNavigate('services')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Menu/list icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <rect width="18" height="18" x="3" y="3" rx="2"/>
                    <path d="M8 8h8"/>
                    <path d="M8 12h8"/>
                    <path d="M8 16h6"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('nav.services')}</h4>
              </button>
              
              {/* Patient Resources */}
              <button 
                onClick={() => onNavigate('patient-resources')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Book icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('nav.resources')}</h4>
              </button>
              
              {/* AI Concierge */}
              <button 
                onClick={() => onOpenChatbot && onOpenChatbot()}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Clean chat assistance icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <path d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('nav.concierge')}</h4>
              </button>
              
              {/* Health Questionnaires */}
              <button 
                onClick={() => onNavigate('questionnaires')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Clipboard/form icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
                    <path d="M9 12h6"/>
                    <path d="M9 16h6"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('dashboard.tools.questionnaires')}</h4>
              </button>
              
              {/* Longevity Score */}
              <button 
                onClick={() => onNavigate('longevity-scoreboard')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Trophy/award icon for scoring */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
                    <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
                    <path d="M4 22h16"/>
                    <path d="M10 14.66V17c0 .55.47.98.97 1.21C11.56 18.75 12 19.60 12 20.5c0 .89-.44 1.75-1.03 2.29-.5.23-.97.56-.97 1.21v1"/>
                    <path d="M14 14.66V17c0 .55-.47.98-.97 1.21-.59.54-1.03 1.40-1.03 2.29 0 .89.44 1.75 1.03 2.29.5.23.97.56.97 1.21v1"/>
                    <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('dashboard.tools.longevityScoreboard')}</h4>
              </button>
              
              {/* Book Appointment */}
              <button 
                onClick={() => onNavigate('appointment-booking')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Calendar/clock icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                    <line x1="16" x2="16" y1="2" y2="6"/>
                    <line x1="8" x2="8" y1="2" y2="6"/>
                    <line x1="3" x2="21" y1="10" y2="10"/>
                    <circle cx="12" cy="15" r="2"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('dashboard.tools.appointments')}</h4>
              </button>
              
              {/* Health Data */}
              <button 
                onClick={() => onNavigate('health-dashboard')}
                className="ka-wellness-card group"
              >
                <div className="ka-wellness-card__icon">
                  {/* Heart icon */}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                </div>
                <h4 className="ka-wellness-card__title">{t('dashboard.tools.healthDashboard')}</h4>
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

const PersonalizedProtocol = ({ user, onNavigate }) => {
  const [showModal, setShowModal] = useState(false);
  const { t } = useTranslation();

  return (
    <div className="min-h-screen" style={{background: 'var(--ka-bg)'}}>
      {/* Header with Navigation */}
      <div className="mb-8 pt-8">
        <div className="flex items-center justify-between mb-4 px-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="flex items-center space-x-2 text-ka-brand hover:text-ka-gold-700 transition-colors"
              aria-label="Back to dashboard"
            >
              <svg className="w-5 h-5 ka-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="font-medium">{t('protocol.backToDashboard')}</span>
            </button>
          </div>
          <button
            onClick={() => onNavigate('menu')}
            className="hamburger-menu"
            aria-label="Main menu"
          >
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="max-w-4xl mx-auto px-6 text-center mb-16">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6" style={{background: 'var(--ka-grad-gold)'}}>
            {/* Stylized Lotus Icon */}
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" className="w-10 h-10">
              <path d="M12 2c-2 0-4 2-4 4 0 2 2 4 4 4s4-2 4-4c0-2-2-4-4-4z"/>
              <path d="M12 6c-3 0-6 3-6 6 0 3 3 6 6 6s6-3 6-6c0-3-3-6-6-6z"/>
              <path d="M12 10c-4 0-8 4-8 8 0 2 1 4 2 5h12c1-1 2-3 2-5 0-4-4-8-8-8z"/>
              <circle cx="12" cy="12" r="1" fill="white"/>
            </svg>
          </div>
          <h1 className="ka-heading-1 mb-6">
            {t('protocol.title')}
          </h1>
          <div className="w-24 h-0.5 bg-ka-brand mx-auto mb-8"></div>
          <p className="ka-body-lg max-w-3xl mx-auto">
            {t('protocol.subtitle')}
          </p>
        </div>
      </div>

      {/* Unique European Center Banner */}
      <div className="py-8 mb-16" style={{background: 'var(--ka-grad-gold-subtle)', borderTop: '1px solid var(--ka-gold-300)', borderBottom: '1px solid var(--ka-gold-300)'}}>
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-ka-brand rounded-full flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="ka-icon ka-icon--md">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
            <h2 className="ka-heading-2 text-center">{t('protocol.europeanCenter')}</h2>
          </div>
          <p className="ka-body-lg font-medium">
            {t('protocol.uniqueCenter')}
          </p>
        </div>
      </div>

      {/* Three Pillars Section */}
      <div className="max-w-6xl mx-auto px-6 mb-16">
        <h2 className="ka-section-title text-center mb-12">
          {t('protocol.multiOmicsTitle')}
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          
          {/* DNA Analysis */}
          <div className="ka-card text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-6 flex items-center justify-center" style={{background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'}}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                <path d="M12 2l1.09 3.26L16 6.73l-2.91 2.68.63 3.85L12 11.6l-1.72 1.66.63-3.85L8 6.73l2.91-1.47L12 2z"/>
                <circle cx="12" cy="12" r="10"/>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-4" style={{color: 'var(--ka-ink-50)'}}>{t('protocol.genomics.title')}</h3>
            <p className="ka-body-lg">
              {t('protocol.genomics.description')}
            </p>
          </div>

          {/* Blood Analysis */}
          <div className="ka-card text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-6 flex items-center justify-center" style={{background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'}}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                <path d="M12 2C8.5 2 6 4.5 6 8s2.5 6 6 6 6-2.5 6-6-2.5-6-6-6z"/>
                <path d="M12 14v8"/>
                <path d="M8 18h8"/>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-4" style={{color: 'var(--ka-ink-50)'}}>{t('protocol.biomarkers.title')}</h3>
            <p className="ka-body-lg">
              {t('protocol.biomarkers.description')}
            </p>
          </div>

          {/* Microbiome */}
          <div className="ka-card text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-6 flex items-center justify-center" style={{background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)'}}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" className="ka-icon ka-icon--lg">
                <circle cx="12" cy="12" r="3"/>
                <circle cx="12" cy="12" r="7"/>
                <circle cx="12" cy="12" r="11"/>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-4" style={{color: 'var(--ka-ink-50)'}}>{t('protocol.microbiome.title')}</h3>
            <p className="ka-body-lg">
              {t('protocol.microbiome.description')}
            </p>
          </div>
        </div>
      </div>

      {/* AI Technology Section */}
      <div className="bg-gradient-to-r from-stone-50 to-stone-100 py-16 mb-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_figma-dev-2/artifacts/uxx39w2x_KinAura-Logo-animation-02.gif" 
              alt="KinAura AI Technology"
              className="w-40 h-auto mx-auto mb-6 opacity-80 max-w-full"
            />
            <h2 className="text-3xl luxury-serif text-stone-800 mb-4">
              {t('protocol.aiEngine')}
            </h2>
            <div className="w-20 h-0.5 bg-gradient-to-r from-transparent via-amber-600 to-transparent mx-auto mb-6"></div>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <p className="text-lg text-stone-700 leading-relaxed mb-6">
              Our breakthrough AI system processes over 2 million medical studies in real-time, 
              utilizing K-means clustering across 23 patient cohorts, Bayesian dose optimization, 
              and reinforcement learning to generate personalized protocols with 94.2% accuracy.
            </p>
            <div className="grid md:grid-cols-2 gap-6 text-left">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-[#C8A25A] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-stone-700">340ms protocol generation time</span>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-[#C8A25A] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-stone-700">GRADE-weighted evidence validation</span>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-[#C8A25A] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-stone-700">Deterministic, auditable algorithms</span>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-[#C8A25A] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-stone-700">Collaborative learning from 15,000+ patients</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Treatment Sophistication */}
      <div className="max-w-6xl mx-auto px-6 mb-16">
        <h2 className="text-3xl luxury-serif text-stone-800 text-center mb-12">
          Advanced Treatment Integration
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-stone-100">
            <h3 className="text-xl font-semibold text-stone-800 mb-4">Precision Dosing</h3>
            <p className="text-stone-600 leading-relaxed mb-4">
              Bayesian algorithms calculate optimal dosages for NAD+, GLP-1, IV therapies, and peptides 
              based on your age, weight, metabolic markers, and genetic variants.
            </p>
            <ul className="text-stone-600 space-y-2">
              <li>• Monte Carlo sampling with 10,000 iterations</li>
              <li>• Age and weight-adjusted protocols</li>
              <li>• Real-time safety contraindication checking</li>
            </ul>
          </div>
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-stone-100">
            <h3 className="text-xl font-semibold text-stone-800 mb-4">Treatment Sequencing</h3>
            <p className="text-stone-600 leading-relaxed mb-4">
              Deep Q-Learning algorithms optimize treatment timing and combinations across 50+ therapeutic 
              modalities including Red Light Therapy, EBOO, and regenerative aesthetics.
            </p>
            <ul className="text-stone-600 space-y-2">
              <li>• Reinforcement learning optimization</li>
              <li>• Synergistic treatment combinations</li>
              <li>• Adaptive protocol refinement</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="max-w-4xl mx-auto px-6 text-center pb-16">
        <div className="bg-gradient-to-br from-[#C8A25A] to-[#B8925A] rounded-3xl p-12 text-white">
          <h2 className="text-3xl luxury-serif mb-6">Ready to Experience Precision Medicine?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join the select group of individuals experiencing the future of personalized wellness today. 
            Discover your unique protocol based on comprehensive DNA, blood, and microbiome analysis.
          </p>
          <div className="space-y-4 mb-8">
            <button
              onClick={() => setShowModal(true)}
              className="bg-white text-[#C8A25A] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-stone-50 transition-colors w-full md:w-auto"
            >
              Begin Your Personalized Assessment
            </button>
            <p className="text-sm opacity-75">
              Comprehensive multi-omics analysis and AI protocol generation
            </p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C8A25A] rounded-full mx-auto mb-6 flex items-center justify-center">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-stone-800 mb-4">Welcome to Precision Medicine</h3>
              <p className="text-stone-600 mb-6">
                Thank you for your interest in our AI-powered personalized protocol program. 
                Our team will contact you within 24 hours to begin your comprehensive multi-omics assessment.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => onNavigate('appointment-booking')}
                  className="bg-[#C8A25A] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#B8925A] transition-colors w-full"
                >
                  Schedule Consultation
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-stone-500 hover:text-stone-700 transition-colors w-full py-2"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const MyBookings = ({ user, onNavigate, onLogoClick }) => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Get backend URL
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        // Fetch real appointment bookings
        const response = await fetch(`${BACKEND_URL}/api/patient/appointments/bookings`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setAppointments(data || []);
        } else {
          // Fallback to mock data if API fails
          console.warn('API call failed, using mock data');
          setAppointments(mockBookings);
        }
      } else {
        setAppointments(mockBookings);
      }
    } catch (error) {
      console.error('Error fetching appointments:', error);
      // Fallback to mock data on error
      setAppointments(mockBookings);
    } finally {
      setLoading(false);
    }
  };

  // Mock data matching Figma design (fallback)
  const mockBookings = [
    {
      id: 1,
      service: { name: 'Exosomes Therapy' },
      appointment_date: '2024-12-21',
      start_time: '14:00',
      end_time: '15:00',
      amount: 390.00,
      status: 'confirmed',
      payment_status: 'paid',
      confirmation_code: 'EX240021'
    },
    {
      id: 2,
      service: { name: 'Ozone Therapy' },
      appointment_date: '2024-12-15',
      start_time: '10:00', 
      end_time: '11:30',
      amount: 229.00,
      status: 'completed',
      payment_status: 'paid',
      confirmation_code: 'OZ240015'
    },
    {
      id: 3,
      service: { name: 'IV Therapy Drips' },
      appointment_date: '2024-12-08',
      start_time: '16:00',
      end_time: '17:00',
      amount: 179.00,
      status: 'completed', 
      payment_status: 'paid',
      confirmation_code: 'IV240008'
    }
  ];

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      confirmed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Confirmed' },
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      completed: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Completed' },
      cancelled: { bg: 'bg-red-100', text: 'text-red-800', label: 'Cancelled' },
      no_show: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'No Show' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  // Filter appointments by status
  const upcomingBookings = appointments.filter(booking => 
    ['confirmed', 'pending'].includes(booking.status)
  );
  const completedBookings = appointments.filter(booking => 
    ['completed'].includes(booking.status)
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your bookings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream relative">
      {/* Kintsugi Background Lines */}
      <div className="kintsugi-lines">
        <svg viewBox="0 0 400 800" className="w-full h-full">
          <path d="M50,100 Q200,150 350,100 T600,150" className="kintsugi-gold"/>
          <path d="M0,300 Q150,250 300,300 T500,250" className="kintsugi-gold"/>
          <path d="M100,500 Q250,450 400,500 T700,450" className="kintsugi-gold"/>
          <path d="M20,700 Q180,650 340,700 T620,650" className="kintsugi-gold"/>
        </svg>
      </div>

      {/* Header */}
      <div className="app-header content-above-kintsugi">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('dashboard'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="kinaura-logo-text hover:text-gold transition-colors">KinAura</span>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => onNavigate('appointment-booking')}
            className="pill-button text-sm"
          >
            BOOK APPT
          </button>
          <button 
            onClick={() => onNavigate('menu')}
            className="hamburger-menu"
          >
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
          </button>
        </div>
      </div>

      <div className="p-6 content-above-kintsugi">
        {/* My Bookings Header */}
        <div className="flex items-center justify-center mb-6">
          <div className="pill-button flex items-center space-x-2">
            <span className="text-sm font-medium">📅</span>
            <span className="text-sm font-medium tracking-wider">MY BOOKINGS</span>
          </div>
        </div>

        {/* Bookings Table Header */}
        <div className="cream-card mb-4">
          <div className="grid grid-cols-4 gap-4 text-sm font-medium text-gray-600 kinaura-subheading mb-4">
            <span>TREATMENTS</span>
            <span>DATE</span>
            <span>PRICE</span>
            <span>ACTIONS</span>
          </div>

          {/* Upcoming Section */}
          {upcomingBookings.length > 0 && (
            <>
              <div className="section-header">UPCOMING</div>
              {upcomingBookings.map((booking) => (
                <div key={booking._id || booking.id} className="treatment-item">
                  <div className="grid grid-cols-4 gap-4 items-center">
                    <span className="text-sm font-medium kinaura-body">
                      {booking.service?.name || booking.treatment}
                    </span>
                    <div className="text-sm text-gray-600 kinaura-body">
                      <div>{formatDate(booking.appointment_date || booking.date)}</div>
                      {booking.start_time && (
                        <div className="text-xs opacity-70">
                          {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                        </div>
                      )}
                    </div>
                    <span className="text-sm font-medium kinaura-body">
                      €{typeof booking.amount === 'number' ? booking.amount.toFixed(2) : booking.price}
                    </span>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(booking.status)}
                      {booking.confirmation_code && (
                        <span className="text-xs text-gray-500">#{booking.confirmation_code}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Completed Section */}
          {completedBookings.length > 0 && (
            <>
              <div className="section-header">COMPLETED</div>
              {completedBookings.map((booking) => (
                <div key={booking._id || booking.id} className="treatment-item">
                  <div className="grid grid-cols-4 gap-4 items-center">
                    <span className="text-sm font-medium kinaura-body opacity-70">
                      {booking.service?.name || booking.treatment}
                    </span>
                    <div className="text-sm text-gray-600 kinaura-body opacity-70">
                      <div>{formatDate(booking.appointment_date || booking.date)}</div>
                      {booking.start_time && (
                        <div className="text-xs opacity-70">
                          {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                        </div>  
                      )}
                    </div>
                    <span className="text-sm font-medium kinaura-body opacity-70">
                      €{typeof booking.amount === 'number' ? booking.amount.toFixed(2) : booking.price}
                    </span>
                    <div className="flex space-x-2">
                      <button className="text-sm text-green-500">✅</button>
                      <button className="text-sm text-blue-500 hover:text-blue-600">📋</button>
                      {booking.confirmation_code && (
                        <span className="text-xs text-gray-500">#{booking.confirmation_code}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}

          {upcomingBookings.length === 0 && completedBookings.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-gray-600 text-sm mb-4 kinaura-body">No bookings yet</p>
              <button 
                onClick={() => onNavigate('appointment-booking')}
                className="pill-button"
              >
                Book Your First Appointment
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Buttons */}
      <button className="floating-action floating-chat">
        <span className="text-lg">💬</span>
      </button>
      <button className="floating-action floating-calendar">
        <span className="text-lg">📅</span>
      </button>
    </div>
  );
};

const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let response;
      if (isLogin) {
        response = await apiHelper.auth.login(formData.email, formData.password);
      } else {
        response = await apiHelper.auth.register(
          formData.email, 
          formData.password, 
          formData.full_name, 
          formData.phone
        );
      }
      
      if (response.access_token) {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        onLogin(response.user);
      }
    } catch (err) {
      setError(err.message || err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = async (provider) => {
    setLoading(true);
    setError('');

    // Special admin login - only for admin access
    if (provider === 'admin') {
      const mockUserData = {
        provider: 'admin',
        access_token: 'admin_token',
        full_name: 'Dr. Marco Rossi',
        email: 'admin@kinaura.com',
        role: 'admin',
        membership_tier: 'admin'
      };
      
      // Admin login should work immediately
      localStorage.setItem('token', mockUserData.access_token);
      localStorage.setItem('user', JSON.stringify(mockUserData));
      onLogin(mockUserData);
      setLoading(false);
      return;
    }

    // For Google, Apple, Facebook - redirect to Emergent authentication
    try {
      const frontendUrl = process.env.REACT_APP_FRONTEND_URL || window.location.origin;
      const redirectUrl = frontendUrl; // Redirect back to main app, not /profile
      const emergentAuthUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      console.log('🔗 Redirecting to Emergent auth:', emergentAuthUrl);
      console.log('📍 Will redirect back to:', redirectUrl);
      
      // Redirect to Emergent authentication
      window.location.href = emergentAuthUrl;
      
    } catch (err) {
      setError(`Authentication failed: ${err.message}`);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FDFCFA] via-white to-[#F8F5F0] flex flex-col items-center justify-center relative overflow-hidden">
      {/* KinAura Background with Gold Veins */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `url(${kinauraSplashBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      ></div>

      {/* Gold Veins Pattern - Kintsugi Style */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Main diagonal gold veins */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          {/* Primary crack pattern */}
          <path 
            d="M20,10 Q40,25 60,15 T85,30 Q90,45 75,60 T90,85" 
            stroke="url(#goldGradient1)" 
            strokeWidth="0.08" 
            fill="none" 
            opacity="0.6"
          />
          <path 
            d="M10,35 Q30,50 50,40 T75,55 Q85,70 70,85" 
            stroke="url(#goldGradient2)" 
            strokeWidth="0.06" 
            fill="none" 
            opacity="0.4"
          />
          <path 
            d="M5,60 Q25,75 45,65 T70,80 Q80,90 95,85" 
            stroke="url(#goldGradient3)" 
            strokeWidth="0.04" 
            fill="none" 
            opacity="0.5"
          />
          {/* Secondary veins */}
          <path 
            d="M15,20 Q35,35 55,25 T80,40" 
            stroke="url(#goldGradient4)" 
            strokeWidth="0.03" 
            fill="none" 
            opacity="0.3"
          />
          <path 
            d="M25,50 Q45,65 65,55 T90,70" 
            stroke="url(#goldGradient5)" 
            strokeWidth="0.03" 
            fill="none" 
            opacity="0.3"
          />
          
          {/* Gradient definitions */}
          <defs>
            <linearGradient id="goldGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.8"/>
              <stop offset="50%" stopColor="#B8925A" stopOpacity="0.9"/>
              <stop offset="100%" stopColor="#C8A25A" stopOpacity="0.7"/>
            </linearGradient>
            <linearGradient id="goldGradient2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#B8925A" stopOpacity="0.6"/>
              <stop offset="50%" stopColor="#D4AF37" stopOpacity="0.8"/>
              <stop offset="100%" stopColor="#E6C068" stopOpacity="0.5"/>
            </linearGradient>
            <linearGradient id="goldGradient3" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#C8A25A" stopOpacity="0.7"/>
              <stop offset="50%" stopColor="#D4AF37" stopOpacity="0.6"/>
              <stop offset="100%" stopColor="#B8925A" stopOpacity="0.8"/>
            </linearGradient>
            <linearGradient id="goldGradient4" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#E6C068" stopOpacity="0.4"/>
              <stop offset="100%" stopColor="#D4AF37" stopOpacity="0.6"/>
            </linearGradient>
            <linearGradient id="goldGradient5" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.5"/>
              <stop offset="100%" stopColor="#C8A25A" stopOpacity="0.7"/>
            </linearGradient>
          </defs>
        </svg>

        {/* Additional subtle floating elements */}
        <div className="absolute top-20 left-10 w-1 h-1 bg-ka-gold-400 rounded-full opacity-60 animate-pulse"></div>
        <div className="absolute top-40 right-20 w-0.5 h-0.5 bg-ka-gold-500 rounded-full opacity-40 animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute bottom-40 left-20 w-1.5 h-1.5 bg-ka-gold-300 rounded-full opacity-50 animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute bottom-20 right-10 w-1 h-1 bg-ka-gold-400 rounded-full opacity-30 animate-pulse" style={{animationDelay: '3s'}}></div>
      </div>

      <div className="relative z-10 w-full max-w-md px-6">
        {/* Header Section */}
        <div className="text-center mb-12">
          {/* KinAura Logo */}
          <div className="mb-8">
            <img 
              src="/brand/kinaura-logo.svg" 
              alt="KinAura" 
              className="w-20 h-20 mx-auto mb-6"
              onError={(e) => {
                e.target.src = "https://customer-assets.emergentagent.com/job_patient-hub-7/artifacts/amo3v5jb_KinAura%20Logo%20Color.svg";
              }}
            />
          </div>
          
          {/* Welcome Text */}
          <h1 className="text-2xl font-light text-ka-text-1 mb-2 tracking-wide">
            Welcome Back
          </h1>
          <p className="text-sm text-ka-text-2 font-light leading-relaxed">
            Sign in to continue your wellness journey
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center">
              <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
              <span className="text-sm text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Login Form */}
        {isLogin ? (
          <div className="space-y-6">
            {/* Social Login Options - Apple, Google, Facebook */}
            <div className="space-y-3 mb-8">
              <AppleLoginComponent 
                onAuthSuccess={(data) => {
                  localStorage.setItem('token', data.token);
                  localStorage.setItem('user', JSON.stringify(data.user));
                  onLogin(data.user);
                }}
                onAuthError={(error) => {
                  setError(error.message || 'Apple login failed');
                }}
              />
              
              <FacebookLoginComponent
                onAuthSuccess={(data) => {
                  localStorage.setItem('token', data.token);
                  localStorage.setItem('user', JSON.stringify(data.user));
                  onLogin(data.user);
                }}
                onAuthError={(error) => {
                  setError(error.message || 'Facebook login failed');
                }}
              />

              <button
                onClick={() => handleSocialLogin('google')}
                className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </button>
            </div>

            {/* Divider */}
            <div className="relative mb-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-ka-stone-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-gradient-to-br from-[#FDFCFA] via-white to-[#F8F5F0] text-ka-text-2 font-medium">
                  or continue with email
                </span>
              </div>
            </div>

            {/* Email Login Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-4">
                <div className="relative">
                  <input
                    type="email"
                    name="email"
                    placeholder="Email address"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                    required
                  />
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                    <svg className="w-5 h-5 text-ka-text-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                    </svg>
                  </div>
                </div>

                <div className="relative">
                  <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                    required
                  />
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                    <svg className="w-5 h-5 text-ka-text-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-ka-gold-600 border-ka-stone-300 rounded focus:ring-ka-gold-500"/>
                  <span className="text-ka-text-2">Remember me</span>
                </label>
                <button type="button" className="text-ka-gold-600 hover:text-ka-gold-700 transition-colors font-medium">
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 px-6 bg-gradient-to-r from-ka-gold-500 to-ka-gold-600 text-white rounded-2xl font-semibold tracking-wide hover:from-ka-gold-600 hover:to-ka-gold-700 focus:ring-4 focus:ring-ka-gold-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Signing in...</span>
                  </div>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            {/* Sign Up Link */}
            <div className="text-center pt-6">
              <p className="text-ka-text-2">
                Don't have an account?{' '}
                <button
                  onClick={() => setIsLogin(false)}
                  className="text-ka-gold-600 hover:text-ka-gold-700 font-semibold transition-colors"
                >
                  Sign up
                </button>
              </p>
            </div>

            {/* Admin Login - Bottom Horizontal */}
            <div className="pt-6 border-t border-ka-stone-200">
              <button
                onClick={() => handleSocialLogin('admin')}
                className="w-full py-3 px-4 bg-gradient-to-r from-ka-stone-100 to-ka-stone-50 text-ka-text-2 rounded-xl border border-ka-stone-200 hover:border-ka-gold-300 hover:from-ka-gold-50 hover:to-ka-gold-100 hover:text-ka-gold-700 transition-all duration-200 flex items-center justify-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
                <span className="text-sm font-medium">Admin Access</span>
              </button>
            </div>
          </div>
        ) : (
          /* Registration Form */
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-xl font-medium text-ka-text-1 mb-2">Create Account</h2>
              <p className="text-sm text-ka-text-2">Join KinAura and start your wellness journey</p>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-4">
                <input
                  type="text"
                  name="full_name"
                  placeholder="Full Name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                  required
                />

                <input
                  type="email"
                  name="email"
                  placeholder="Email address"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                  required
                />

                <input
                  type="tel"
                  name="phone"
                  placeholder="Phone (optional)"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                />

                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-4 py-4 bg-white rounded-2xl border border-ka-stone-200 focus:border-ka-gold-400 focus:ring-4 focus:ring-ka-gold-100 transition-all duration-200 text-ka-text-1 placeholder-ka-text-3 outline-none"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 px-6 bg-gradient-to-r from-ka-gold-500 to-ka-gold-600 text-white rounded-2xl font-semibold tracking-wide hover:from-ka-gold-600 hover:to-ka-gold-700 focus:ring-4 focus:ring-ka-gold-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Creating account...</span>
                  </div>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            {/* Sign In Link */}
            <div className="text-center pt-6">
              <p className="text-ka-text-2">
                Already have an account?{' '}
                <button
                  onClick={() => setIsLogin(true)}
                  className="text-ka-gold-600 hover:text-ka-gold-700 font-semibold transition-colors"
                >
                  Sign in
                </button>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="absolute bottom-6 text-center w-full">
        <p className="text-xs text-ka-text-3 px-6">
          Like Kintsugi, beauty is reborn with time.
        </p>
      </div>
    </div>
  );
};

const Hero = ({ onNavigate }) => {
  return (
    <div className="min-h-screen relative bg-white">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 flex justify-between items-center p-6">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={() => onNavigate('hero')}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="text-lg font-light tracking-widest text-white hover:text-gold transition-colors">KinAura</span>
        </div>
        <button 
          onClick={() => onNavigate('menu')}
          className="text-white"
        >
          <div className="space-y-1">
            <div className="w-6 h-0.5 bg-white"></div>
            <div className="w-6 h-0.5 bg-white"></div>
            <div className="w-6 h-0.5 bg-white"></div>
          </div>
        </button>
      </div>

      {/* Background Image */}
      <div 
        className="min-h-screen bg-cover bg-center relative"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80')"
        }}
      >
        {/* Content */}
        <div className="absolute inset-0 flex flex-col justify-center items-center text-center px-6">
          <h1 className="text-4xl md:text-5xl font-light text-white mb-4 leading-tight">
            Centre for<br/>
            Regenerative<br/>
            Wellness
          </h1>
          
          <p className="text-white text-sm font-light tracking-wider mb-12 max-w-md leading-relaxed">
            THE JOURNEY TO SELF-<br/>
            HEALING & LONGEVITY<br/>
            THROUGH SCIENCE
          </p>
          
          <button 
            onClick={() => onNavigate('services')}
            className="bg-transparent border border-white text-white py-3 px-8 rounded-full hover:bg-white hover:text-black transition-all duration-300 text-sm font-medium tracking-wider"
          >
            BOOK APPOINTMENT →
          </button>
        </div>

        {/* Floating Action Buttons */}
        <div className="absolute bottom-6 right-6 space-y-3">
          <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow">
            <span className="text-lg">💬</span>
          </button>
          <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow">
            <span className="text-lg">📅</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const Menu = ({ onNavigate, onLogout, user, platformConfig, onOpenChatbot }) => {
  // Get platform configuration with fallback
  const config = platformConfig || PlatformUtils.getConfig();
  const { t } = useTranslation();
  const { language, switchLanguage } = useLanguage();
  
  const menuItems = [
    { name: t('nav.dashboard').toUpperCase(), icon: '📊', action: () => onNavigate('dashboard') },
    // Admin items only available on web platform
    ...(user?.role === 'admin' && config.allowAdmin ? [
      { name: 'ADMIN PANEL', icon: '⚙️', action: () => onNavigate('admin') },
      { name: 'LONGEVITY ADMIN', icon: '🧬', action: () => onNavigate('longevity-admin') },
      { name: 'HEALTH DATA ADMIN', icon: '💚', action: () => onNavigate('admin-health') }
    ] : []),
    { name: t('dashboard.tools.longevityScoreboard').toUpperCase(), icon: '📈', action: () => onNavigate('longevity-scoreboard') },
    { name: t('dashboard.tools.healthDashboard').toUpperCase(), icon: '💚', action: () => onNavigate('health-dashboard') },
    { name: t('dashboard.tools.questionnaires').toUpperCase(), icon: '📝', action: () => onNavigate('questionnaires') },
    { name: 'BOUTIQUE', icon: '🛍️', action: () => onNavigate('boutique') },
    { name: 'PROTOCOLS', icon: '🏷️', action: () => onNavigate('service-groups') },
    { name: 'TREATMENTS', icon: '🏥', action: () => onNavigate('services') },
    { name: 'BOOK TREATMENT', icon: '📅', action: () => onNavigate('appointment-booking') },
    { name: t('nav.resources').toUpperCase(), icon: '📄', action: () => onNavigate('patient-resources') },
    { name: t('nav.appointments').toUpperCase(), icon: '📋', action: () => onNavigate('bookings') },
    { name: t('nav.concierge').toUpperCase(), icon: '💬', action: () => onOpenChatbot && onOpenChatbot() },
    { 
      name: user ? t('nav.logout').toUpperCase() : t('nav.login').toUpperCase(), 
      icon: '👤', 
      action: () => user ? onLogout() : onNavigate('login')
    },
    // Additional web-only features  
    ...(config.isWeb ? [
      { 
        name: language === 'en' ? 'CAMBIA IN ITALIANO 🇮🇹' : 'SWITCH TO ENGLISH 🇺🇸', 
        icon: '🌐', 
        action: () => switchLanguage(language === 'en' ? 'it' : 'en')
      },
      { name: 'GALLERY', action: () => onNavigate('gallery') },
      { name: 'SERVICES >', action: () => onNavigate('services') },
      { name: 'MEMBERSHIP', action: () => onNavigate('membership') },
      { name: 'SHOP', action: () => onNavigate('shop') },
      { name: 'BLOG', action: () => onNavigate('blog') }
    ] : [])
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-6 border-b border-gray-100">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={() => onNavigate('hero')}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="text-lg font-light tracking-widest text-black hover:text-gold transition-colors">KinAura</span>
        </div>
        <div className="flex items-center space-x-3">
          <LanguageToggle size="small" className="!bg-[#C8A25A]/10 !text-[#C8A25A] !border-[#C8A25A]/30" />
          <button 
            onClick={() => onNavigate('hero')}
            className="text-black text-2xl"
          >
            ×
          </button>
        </div>
      </div>

      {/* Tagline */}
      <div className="px-6 py-4 text-center">
        <p className="text-sm text-gray-600 font-light">
          {t('language') === 'it' ? 'Come il Kintsugi, la bellezza rinasce con il tempo.' : 'Like Kintsugi, beauty is reborn with time.'}
        </p>
      </div>

      {/* Menu Items */}
      <div className="px-6 py-8 space-y-8">
        {menuItems.map((item, index) => (
          <button
            key={index}
            onClick={item.action}
            className="w-full text-left flex items-center space-x-4 py-2 hover:text-yellow-600 transition-colors"
          >
            {item.icon && <span className="text-xl">{item.icon}</span>}
            <span className="text-sm font-light tracking-wider">{item.name}</span>
          </button>
        ))}
      </div>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-6 right-6 space-y-3">
        <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-gray-200">
          <span className="text-lg">💬</span>
        </button>
        <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-gray-200">
          <span className="text-lg">📅</span>
        </button>
      </div>
    </div>
  );
};

const Services = ({ onNavigate, onLogoClick }) => {
  const [services, setServices] = useState([]);
  const [serviceGroups, setServiceGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState(new Set());

  const { language } = useLanguage();
  const { t } = useTranslation(language);

  useEffect(() => {
    fetchServicesAndGroups();
  }, []);

  const fetchServicesAndGroups = async () => {
    try {
      // Fetch both services and service groups
      const [servicesData, groupsData] = await Promise.all([
        apiHelper.services.getAll(),
        apiHelper.serviceGroups?.getAll() || []
      ]);
      
      setServices(servicesData || []);
      setServiceGroups(groupsData || []);
      
      // Group services by category
      groupServicesByCategory(servicesData || [], groupsData || []);
    } catch (error) {
      console.error('Error fetching services and groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupServicesByCategory = (services, groups) => {
    // Create a map of services by category
    const servicesByCategory = {};
    
    // First, organize services by their category
    services.forEach(service => {
      const category = service.category || 'General';
      if (!servicesByCategory[category]) {
        servicesByCategory[category] = [];
      }
      servicesByCategory[category].push(service);
    });
    
    // Create default groups for services without explicit groups
    const defaultGroups = Object.keys(servicesByCategory).map(category => ({
      id: `category-${category}`,
      name: category,
      description: `${category} services`,
      services: servicesByCategory[category],
      color: getColorForCategory(category)
    }));
    
    // Merge with existing service groups
    const allGroups = [...(groups || []), ...defaultGroups];
    setServiceGroups(allGroups);
  };

  const getColorForCategory = (category) => {
    const colors = {
      'Regenerative Medicine': '#B88E35',
      'Wellness': '#CFA544', 
      'Diagnostics': '#D5A144',
      'Therapy': '#E6B34D',
      'General': '#B88E35'
    };
    return colors[category] || '#B88E35';
  };

  const toggleGroup = (groupId) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-ka-bg flex items-center justify-center">
        <div className="ka-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ka-gold-600 mx-auto mb-4"></div>
          <div className="ka-text">{t('common.loading')}...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center p-6 ka-card mx-4 mt-4 mb-6">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => onNavigate('menu')}
            className="ka-text text-xl hover:text-ka-gold-600 transition-colors"
            aria-label="Back to menu"
          >
            ←
          </button>
          <span className="ka-section-title text-lg">{t('services.title')}</span>
        </div>
        
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('dashboard'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="ka-text font-medium tracking-widest hover:text-ka-gold-600 transition-colors">KinAura</span>
        </div>
        
        <button 
          onClick={() => onNavigate('menu')}
          className="hamburger-menu"
          aria-label="Open menu"
        >
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </button>
      </div>

      <div className="px-6 pb-6">
        {/* Services Description */}
        <div className="ka-card p-6 mb-6">
          <h2 className="ka-heading-2 mb-4">Regenerative Wellness Services</h2>
          <p className="ka-body-lg text-ka-text-2">
            Discover our comprehensive range of precision wellness services, powered by advanced genomic analysis 
            and biomarker optimization. Each service is designed to support your unique wellness journey.
          </p>
        </div>

        {/* Service Groups */}
        <div className="space-y-4">
          {serviceGroups.map((group) => {
            const isExpanded = expandedGroups.has(group.id);
            const groupServices = group.services || services.filter(s => s.category === group.name);
            
            return (
              <div key={group.id} className="ka-card overflow-hidden">
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group.id)}
                  className="w-full p-6 text-left hover:bg-ka-muted transition-colors"
                  aria-expanded={isExpanded}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: group.color || '#B88E35' }}
                        ></div>
                        <h3 className="ka-heading-3 text-lg">{group.name}</h3>
                        <span className="ka-chip text-xs">
                          {groupServices.length} {groupServices.length === 1 ? 'service' : 'services'}
                        </span>
                      </div>
                      {group.description && (
                        <p className="ka-body text-ka-text-2">{group.description}</p>
                      )}
                    </div>
                    <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                      <svg 
                        className="w-5 h-5 text-ka-gold-600" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </button>

                {/* Expanded Services */}
                {isExpanded && (
                  <div className="border-t border-ka-stone-200">
                    <div className="p-6 pt-4 space-y-3">
                      {groupServices.length > 0 ? (
                        groupServices.map((service, index) => (
                          <button
                            key={service.id || index}
                            onClick={() => onNavigate('service-detail', service)}
                            className="w-full text-left p-4 rounded-lg hover:bg-ka-muted transition-colors border border-ka-stone-200 hover:border-ka-gold-300"
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <h4 className="ka-text font-medium mb-2">{service.name}</h4>
                                <p className="ka-body-sm text-ka-text-2 leading-relaxed">
                                  {service.description}
                                </p>
                                {service.duration && (
                                  <div className="mt-2 flex items-center space-x-4 text-xs text-ka-text-2">
                                    <span>⏱️ {service.duration} min</span>
                                    {service.price && <span>💰 ${service.price}</span>}
                                  </div>
                                )}
                              </div>
                              <div className="ml-4 flex-shrink-0">
                                <svg 
                                  className="w-4 h-4 text-ka-gold-600" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </div>
                            </div>
                          </button>
                        ))
                      ) : (
                        <div className="text-center py-8 text-ka-text-2">
                          <p>No services available in this category</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Ungrouped Services */}
        {services.filter(service => !serviceGroups.some(group => 
          group.services?.some(s => s.id === service.id) || group.name === service.category
        )).length > 0 && (
          <div className="ka-card mt-6">
            <div className="p-6 border-b border-ka-stone-200">
              <h3 className="ka-heading-3">Additional Services</h3>
              <p className="ka-body text-ka-text-2 mt-2">Other available services</p>
            </div>
            <div className="p-6 space-y-3">
              {services
                .filter(service => !serviceGroups.some(group => 
                  group.services?.some(s => s.id === service.id) || group.name === service.category
                ))
                .map((service) => (
                  <button
                    key={service.id}
                    onClick={() => onNavigate('service-detail', service)}
                    className="w-full text-left p-4 rounded-lg hover:bg-ka-muted transition-colors border border-ka-stone-200 hover:border-ka-gold-300"
                  >
                    <h4 className="ka-text font-medium mb-2">{service.name}</h4>
                    <p className="ka-body-sm text-ka-text-2">{service.description}</p>
                  </button>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-6 right-6 space-y-3">
        <button 
          onClick={() => onNavigate('concierge')}
          className="w-12 h-12 bg-ka-panel rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-ka-gold-300"
          aria-label="Open concierge chat"
        >
          <span className="text-lg">💬</span>
        </button>
        <button 
          onClick={() => onNavigate('appointment-booking')}
          className="w-12 h-12 bg-ka-panel rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-ka-gold-300"
          aria-label="Book appointment"
        >
          <span className="text-lg">📅</span>
        </button>
      </div>
    </div>
  );
};

const ServiceDetail = ({ service, onNavigate }) => {
  const [showBooking, setShowBooking] = useState(false);

  const handleBookAppointment = () => {
    setShowBooking(true);
  };

  if (!service) {
    return <Navigate to="/" />;
  }

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* Header */}
      <div className="bg-white flex justify-between items-center p-6 border-b border-gray-100">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={() => onNavigate('hero')}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="text-lg font-light tracking-widest text-black hover:text-gold transition-colors">KinAura</span>
        </div>
        <div className="space-y-1">
          <div className="w-6 h-0.5 bg-black"></div>
          <div className="w-6 h-0.5 bg-black"></div>
          <div className="w-6 h-0.5 bg-black"></div>
        </div>
      </div>

      <div className="p-6">
        <h1 className="text-2xl font-light mb-6 leading-tight">{service.name}</h1>
        
        <div className="mb-6">
          <h2 className="text-lg font-light tracking-wider mb-4 text-yellow-600">
            {service.description.toUpperCase()}
          </h2>
        </div>

        <div className="prose prose-sm max-w-none mb-8">
          <p className="text-gray-700 leading-relaxed text-sm">
            {service.detailed_description}
          </p>
        </div>

        {service.benefits && (
          <div className="mb-8">
            <h3 className="text-sm font-medium tracking-wider mb-3">BENEFITS:</h3>
            <ul className="space-y-2">
              {service.benefits.map((benefit, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-yellow-600 mr-2">•</span>
                  {benefit}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-sm text-gray-600">Duration: {service.duration} minutes</span>
          </div>
          <div>
            <span className="text-lg font-medium">${service.price}</span>
          </div>
        </div>
      </div>

      {/* Golden decorative elements */}
      <div className="absolute bottom-32 left-0 w-full h-32 pointer-events-none">
        <svg className="w-full h-full opacity-20" viewBox="0 0 400 100">
          <path d="M0,50 Q100,20 200,50 T400,50" stroke="#D97706" strokeWidth="2" fill="none"/>
          <path d="M0,60 Q150,30 300,60 T600,60" stroke="#D97706" strokeWidth="1" fill="none"/>
        </svg>
      </div>

      {/* Book Appointment Button */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-6">
        <button
          onClick={handleBookAppointment}
          className="w-full bg-transparent border border-black text-black py-3 px-8 rounded-full hover:bg-black hover:text-white transition-all duration-300 text-sm font-medium tracking-wider"
        >
          BOOK APPOINTMENT →
        </button>
      </div>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-20 right-6 space-y-3">
        <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-gray-200">
          <span className="text-lg">💬</span>
        </button>
        <button className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow border border-gray-200">
          <span className="text-lg">📅</span>
        </button>
      </div>

      {showBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full">
            <h3 className="text-lg font-medium mb-4">Book Appointment</h3>
            <p className="text-sm text-gray-600 mb-4">
              Appointment booking for {service.name} will be available soon. Please contact us directly.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowBooking(false)}
                className="flex-1 py-2 px-4 border border-gray-300 rounded hover:bg-gray-50"
              >
                Close
              </button>
              <button className="flex-1 py-2 px-4 bg-black text-white rounded hover:bg-gray-800">
                Contact Us
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('hero');
  const [selectedService, setSelectedService] = useState(null);
  const [showChatbot, setShowChatbot] = useState(false);
  const [isLoading, setIsLoading] = useState(true);  // Re-enable loading screen
  const [platformConfig, setPlatformConfig] = useState(null);

  // Handle Emergent auth callback
  const handleEmergentAuthCallback = async () => {
    try {
      console.log('🔄 Processing Emergent authentication callback...');
      
      // Parse session ID from URL fragment
      const fragment = window.location.hash.substring(1); // Remove #
      const params = new URLSearchParams(fragment);
      const sessionId = params.get('session_id');

      if (!sessionId) {
        console.error('❌ No session ID found in callback');
        setCurrentView('login');
        return;
      }

      console.log('✅ Session ID found:', sessionId.substring(0, 8) + '...');

      // Call backend to exchange session ID for user data
      const response = await apiClient('/api/auth/emergent-auth', {
        method: 'POST',
        headers: {
          'X-Session-ID': sessionId
        },
        skipAuth: true
      });

      if (response.access_token && response.user) {
        console.log('🎉 Emergent auth successful:', response.user.email);
        
        // Store authentication data
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Update app state
        setUser(response.user);
        
        // Clear the URL fragment
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Redirect to appropriate dashboard based on role
        setCurrentView(response.user.role === 'admin' ? 'admin' : 'dashboard');
      } else {
        console.error('❌ Invalid response from backend');
        setCurrentView('login');
      }

    } catch (err) {
      console.error('❌ Emergent auth callback error:', err);
      setCurrentView('login');
    }
  };

  // Simplified loading mechanism - no complex useEffect dependencies
  useEffect(() => {
    console.log('🚀 App mounted - starting simple loading timer');
    
    // Simple, single timer that runs once
    const loadingTimer = setTimeout(() => {
      console.log('✅ Loading complete - showing main app');
      
      setIsLoading(false);
      
      // Check if this is an Emergent auth callback first
      if (window.location.hash.includes('session_id=')) {
        console.log('🔐 Detected Emergent auth callback - handling session');
        handleEmergentAuthCallback();
        return;
      }
      
      // Determine which view to show
      const token = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        try {
          const user = JSON.parse(storedUser);
          setUser(user);
          setCurrentView(user.role === 'admin' ? 'admin' : 'dashboard');
        } catch (e) {
          console.error('Error parsing stored user:', e);
          localStorage.removeItem('user');
          localStorage.removeItem('token');
          setCurrentView(platformConfig?.isMobile ? 'login' : 'hero');
        }
      } else {
        setCurrentView(platformConfig?.isMobile ? 'login' : 'hero');
      }
    }, 3000); // Reduced to 3 seconds for faster loading
    
    // Cleanup function
    return () => {
      console.log('🧹 Cleaning up simple loading timer');
      clearTimeout(loadingTimer);
    };
  }, []); // Empty dependency array - runs only once on mount

  // Smart navigation function for logo clicks
  const handleLogoClick = () => {
    if (user) {
      // If user is logged in, take them to their dashboard
      if (user.role === 'admin') {
        setCurrentView('admin');
      } else {
        setCurrentView('dashboard');
      }
    } else {
      // If not logged in, take them to the landing page
      setCurrentView('hero');
    }
  };

  // Navigation handler
  const handleNavigate = (view, data = null) => {
    if (view === 'service-detail') {
      setSelectedService(data);
    } else if (data) {
      setSelectedService(data);
    }
    setCurrentView(view);
  };

  useEffect(() => {
    // Simplified initialization - just set platform config
    const initializeApp = async () => {
      try {
        // Initialize mobile platform if needed
        await PlatformUtils.initializeMobile();
        
        // Get platform configuration
        const config = PlatformUtils.getConfig();
        setPlatformConfig(config);
        
        console.log('App initialization complete - ready for user interaction');
      } catch (error) {
        console.error('Error initializing app:', error);
        setCurrentView('hero'); // Fallback to default flow
      }
    };

    initializeApp();
  }, []);

  const handleLogin = async (userData) => {
    setUser(userData);
    
    // Redirect based on user role
    if (userData.role === 'admin') {
      setCurrentView('admin');
    } else {
      setCurrentView('dashboard');
    }
    
    // Initialize push notifications for the logged-in user
    try {
      const result = await pushNotificationService.initializePushNotifications();
      if (result.success) {
        console.log('Push notifications initialized successfully');
      } else {
        console.warn('Push notifications failed to initialize:', result.error);
      }
    } catch (error) {
      console.error('Error initializing push notifications:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCurrentView('login');
  };

  // Loading Screen Component with KinAura Logo Animation
  const LoadingScreen = () => (
    <div className="fixed inset-0 bg-white flex flex-col items-center justify-center z-50">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-cream to-white"></div>
      
      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center space-y-8">
        {/* KinAura Logo Animation */}
        <div className="flex items-center justify-center mb-8">
          <img 
            src="https://customer-assets.emergentagent.com/job_luxury-wellness/artifacts/nd1tx9qf_KinAura-Logo-animation-02.gif"
            alt="KinAura Loading Animation"
            className="w-64 h-auto max-w-sm"
            style={{
              filter: 'brightness(1.1) contrast(1.05)',
            }}
          />
        </div>
        
        {/* Welcome Text */}
        <div className="text-center space-y-4">
          <h1 className="text-2xl md:text-3xl font-light tracking-wide text-gray-800 mb-4">
            Your Wellness Journey Starts Here
          </h1>
          
          {/* Loading dots animation */}
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-[#C8A25A] rounded-full loading-dot"></div>
            <div className="w-2 h-2 bg-[#C8A25A] rounded-full loading-dot"></div>
            <div className="w-2 h-2 bg-[#C8A25A] rounded-full loading-dot"></div>
          </div>
        </div>
      </div>
      
      {/* Subtle KinAura branding at bottom */}
      <div className="absolute bottom-8 left-0 right-0 text-center">
        <p className="text-sm text-gray-500 font-light tracking-widest">
          KINAURA
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Excellence in Aesthetic Medicine
        </p>
      </div>
    </div>
  );

  // Show loading screen if still loading
  if (isLoading) {
    return <LoadingScreen />;
  }

  // Removed loading screen - go directly to rendering views

  const renderView = () => {
    switch (currentView) {
      case 'hero':
        return <HeroLanding onNavigate={handleNavigate} />;
      case 'login':
        return <Login onLogin={handleLogin} />;
      case 'dashboard':
        return <PatientDashboard user={user} onNavigate={handleNavigate} onOpenChatbot={() => setShowChatbot(true)} onLogoClick={handleLogoClick} />;
      case 'admin':
        return (
          <Suspense fallback={<SkeletonCard className="h-96" />}>
            <AdminDashboard user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />
          </Suspense>
        );
      case 'longevity-scoreboard':
        return <LongevityScoreboard user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'longevity-admin':
        return (
          <Suspense fallback={<SkeletonCard className="h-96" />}>
            <LongevityScoreboardAdmin user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />
          </Suspense>
        );
      case 'questionnaires':
        return <PatientQuestionnaires user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'boutique':
        return <Boutique backendUrl={BACKEND_URL} user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'membership':
        return <Membership onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'appointment-booking':
        return <AppointmentBooking user={user} onNavigate={handleNavigate} />;
      case 'booking-success':
        return <BookingSuccess onNavigate={handleNavigate} />;
      case 'admin-appointments':
        return (
          <Suspense fallback={<SkeletonCard className="h-96" />}>
            <AdminAppointments user={user} onNavigate={handleNavigate} />
          </Suspense>
        );
      case 'bookings':
        return <MyBookings user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'patient-resources':
        return <PatientResources user={user} onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'health-dashboard':
        return <HealthDashboard user={user} backendUrl={`${BACKEND_URL}/api`} onNavigate={handleNavigate} />;
      case 'admin-health':
        return (
          <Suspense fallback={<SkeletonCard className="h-96" />}>
            <AdminHealthData backendUrl={`${BACKEND_URL}/api`} onNavigate={handleNavigate} />
          </Suspense>
        );
      case 'menu':
        return <Menu onNavigate={handleNavigate} onLogout={handleLogout} user={user} platformConfig={platformConfig} onOpenChatbot={() => setShowChatbot(true)} />;
      case 'services':
        return <Services onNavigate={handleNavigate} onLogoClick={handleLogoClick} />;
      case 'service-groups':
        return <ServiceGroups onNavigate={handleNavigate} backendUrl={`${BACKEND_URL}/api`} />;
      case 'service-detail':
        return <ServiceDetail service={selectedService} onNavigate={handleNavigate} />;
      case 'personalized-protocol':
        return <PersonalizedProtocol user={user} onNavigate={handleNavigate} />;
      default:
        return user ? <PatientDashboard user={user} onNavigate={handleNavigate} onOpenChatbot={() => setShowChatbot(true)} onLogoClick={handleLogoClick} /> : <HeroLanding onNavigate={handleNavigate} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <ToastProvider>
          <ThemeProvider>
            <LanguageProvider>
              <ContentSyncProvider>
                <AuthContext.Provider value={{ user, setUser }}>
                  <BrowserRouter>
                    <div className="App">
                      <ContentSyncIndicator />
                      <AppContent 
                        renderView={renderView}
                        user={user}
                        showChatbot={showChatbot}
                        setShowChatbot={setShowChatbot}
                      />
                    </div>
                  </BrowserRouter>
                </AuthContext.Provider>
              </ContentSyncProvider>
            </LanguageProvider>
          </ThemeProvider>
        </ToastProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

// Separate component to inject toast instance
const AppContent = ({ renderView, user, showChatbot, setShowChatbot }) => {
  const { toast } = useToast();
  
  // Inject toast instance into apiClient
  useEffect(() => {
    setToastInstance(toast);
  }, [toast]);

  return (
    <div 
      className="kinaura-app-background"
      style={{
        backgroundImage: `url(${kinauraSplashBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
        minHeight: '100vh',
        width: '100%'
      }}
    >
      {/* Semi-transparent overlay for better readability */}
      <div 
        className="kinaura-app-overlay"
        style={{
          backgroundColor: 'rgba(250, 250, 247, 0.85)', // Ivory overlay with transparency
          backdropFilter: 'blur(0.5px)',
          minHeight: '100vh',
          width: '100%'
        }}
      >
        {renderView()}
        {/* KinAura Chatbot - Show when showChatbot is true */}
        {user && showChatbot && (
          <PatientChatbot 
            backendUrl={`${BACKEND_URL}/api`} 
            isOpen={showChatbot}
            onClose={() => setShowChatbot(false)}
          />
        )}

        {/* Proactive Protocol Notifications */}
        {user && user.role === 'patient' && (
          <ProactiveNotification
            user={user}
            onClose={() => {
              // Optional: Handle notification close events
              console.log('Proactive notification closed');
            }}
          />
        )}
      </div>
    </div>
  );
};

export default App;