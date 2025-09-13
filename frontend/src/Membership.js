import React from 'react';
import { useLanguage } from './contexts/LanguageContext';

const Membership = ({ onNavigate, onLogoClick }) => {
  const { language } = useLanguage();

  const tiers = [
    {
      id: 'gold',
      name: 'GOLD MEMBERSHIP',
      tagline: 'The gateway to your personalized regenerative journey — powered by science and guided by AI.',
      description: 'The Gold Membership marks your exclusive entry into the KinAura ecosystem: a refined experience that integrates advanced diagnostics, regenerative medicine, and bespoke treatments into a continuous, high-touch path designed for those committed to investing in their long-term biological health and natural beauty.',
      startText: 'Your journey begins with the KinAura Discovery Protocol — a comprehensive set of genetic, microbiota, and biomarker analyses. From these, we generate your personal Bioregen Index, a proprietary indicator that allows our AI system to design your Regenerative Sequence: a dynamic, adaptive roadmap of targeted treatments, tailored to your unique biology and evolving over time.',
      includes: [
        'A full-spectrum diagnostic check-up to assess your baseline health and regenerative potential',
        'Access to a curated selection of face and body treatments — such as Morpheus8, Ultraformer, IV Therapy, Red Light + HBOT, and customized skincare — integrated into your personalized Regenerative Sequence',
        'Ongoing clinical reviews to monitor progress and refine your protocol',
        'A rhythm of bi-weekly treatments, aligned with your individual biomarkers, goals, and lifestyle'
      ],
      privileges: [
        'Preferential access to additional treatments, advanced technologies, and specialist consultations',
        'Invitations to private events, expert workshops, and curated gatherings within the KinAura Social Wellness Lounge',
        'Dedicated concierge service for seamless scheduling, communication, and ongoing therapeutic coordination'
      ],
      cta: 'Apply Now to Reserve your Spot',
      color: 'from-yellow-400 to-amber-600',
      bgColor: 'bg-gradient-to-br from-amber-50 to-yellow-100',
      textColor: 'text-amber-900',
      image: 'https://customer-assets.emergentagent.com/job_luxury-health-1/artifacts/w67qfdcd_image%20gold.webp'
    },
    {
      id: 'platinum',
      name: 'PLATINUM MEMBERSHIP',
      tagline: 'A continuous, high-frequency optimization program — where every detail is personalized, every protocol intelligent, and every experience reserved.',
      description: 'The Platinum Membership is KinAura\'s most complete clinical journey short of our Elite invitation-only tier. Designed for those seeking sustained transformation and peak biological performance, it offers unmatched access to advanced regenerative technologies, deeper diagnostic insight, and a higher cadence of curated interventions.',
      startText: 'As with all KinAura memberships, your journey begins with the Discovery Protocol and the generation of your Bioregen Index — the foundation for your Regenerative Sequence, continuously updated through AI based on your biomarker trends, lifestyle evolution, and therapeutic response.',
      includes: [
        'A personalized program of frequent, high-impact treatments selected from the full Gold-tier offering, along with exclusive Platinum protocols — including exosome facials, advanced IV therapy stacks (e.g., NAD+ + methylene blue + mineral blend), PRP or polynucleotide biostimulation, and Hyperbaric Oxygen Therapy',
        'Quarterly clinical upgrades, including a full Longevity Lab Report with biological age analysis and biomarker tracking, followed by AI-guided protocol refinement',
        'In-depth hormonal and peptide consults for targeted anti-aging interventions',
        'Ongoing skincare customization sessions, reformulated as your skin evolves',
        'Seamless support and program modulation through your dedicated KinAura concierge'
      ],
      privileges: [
        'Exclusive access to technology pilots and pre-launch protocols, available only to KinAura Platinum and R&D clients',
        'Private invitations to speaker dinners, scientific workshops, and wellness events curated for our inner circle',
        'Access to the Platinum Lounge and eligibility for KinAura retreats and global concierge care',
        'No blackout periods. No need to book in advance — your schedule is our schedule. As a Platinum member, you enjoy continuous, on-demand access to the KinAura experience. We\'re always here for you.'
      ],
      cta: 'Apply Now to Reserve your Spot',
      color: 'from-slate-400 to-gray-700',
      bgColor: 'bg-gradient-to-br from-slate-50 to-gray-100',
      textColor: 'text-slate-900',
      image: 'https://customer-assets.emergentagent.com/job_luxury-health-1/artifacts/mmtesr0t_image%20platinum.webp'
    },
    {
      id: 'elite',
      name: 'ELITE MEMBERSHIP',
      tagline: 'More than care — devotion.',
      description: 'The KinAura Elite Membership is not a program. It\'s a world built around you. Designed for a select few, it offers a level of personalization, presence, and protection that redefines what care means.',
      startText: 'Imagine having a dedicated team that knows your biology, your rhythms, your needs — sometimes better than you do. A team that anticipates. That removes friction. That elevates every detail of your wellbeing, so you can simply live, thrive, and perform — without ever having to ask twice.',
      additionalText: 'Your protocol is continuously refined by our most advanced AI engine, integrating real-time biomarker evolution, life phase transitions, and cutting-edge research. But what makes Elite different is not just the data — it\'s the devotion.',
      includes: [
        'Unlimited access to all KinAura technologies, treatments, and diagnostics, fully modulated and managed by your dedicated medical team',
        'Quarterly longevity retreats and at-home sessions, curated specifically for your biological and lifestyle needs',
        'Ongoing hormonal, genomic, and peptide optimization, with continuous feedback loops between you and your clinicians',
        'On-demand skincare formulation and supplement delivery, as your needs evolve',
        'A private, personal concierge who handles everything from scheduling to home preparation, travel alignment, and post-session integration',
        'Discreet pickup and drop-off service, because you should never have to stress about logistics when you\'re investing in your future self'
      ],
      closingText: 'You don\'t need to plan — we\'re already two steps ahead. We hold space for your evolution. We remove pressure. We give you back time. And we ensure that your journey toward peak biological performance and aesthetic refinement is as seamless, private, and powerful as it deserves to be.',
      cta: 'By Invitation Only',
      color: 'from-gray-900 via-black to-gray-800',
      bgColor: 'bg-gradient-to-br from-gray-50 to-slate-100',
      textColor: 'text-gray-900',
      image: 'https://web.kinauramed.com/_next/image?url=https%3A%2F%2Fmedia.diamondincision.it%2Fplans%2Fdev-3U-1746734282341.png&w=1080&q=75'
    }
  ];

  return (
    <div className="min-h-screen bg-cream">
      {/* Navigation Header */}
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
          {/* Back Button */}
          <button 
            onClick={() => onNavigate('dashboard')}
            className="flex items-center space-x-1 text-gray-700 hover:text-[#C8A25A] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">{language === 'it' ? 'Indietro' : 'Back'}</span>
          </button>
          
          {/* Hamburger Menu */}
          <button 
            onClick={() => onNavigate('menu')}
            className="hamburger-menu flex flex-col space-y-1 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Open menu"
          >
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="bg-gradient-to-br from-[#C8A25A] to-[#B88E35] text-white py-16">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-light mb-6 tracking-wide">
            KinAura Memberships
          </h1>
          <p className="text-xl md:text-2xl font-light mb-4 text-white text-opacity-90">
            Join the First Longevity Social Wellness Club
          </p>
          <p className="text-lg font-light text-white text-opacity-80 max-w-3xl mx-auto">
            Our Memberships are designed to offer not just care, but also connection, growth, and belonging.
          </p>
        </div>
      </div>

      {/* Membership Tiers */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="space-y-16">
          {tiers.map((tier, index) => (
            <div key={tier.id} className={`ka-card p-8 md:p-12 ${tier.bgColor} border-2 border-opacity-20`}>
              {/* Tier Header */}
              <div className="text-center mb-8">
                <div className={`inline-block px-6 py-2 rounded-full bg-gradient-to-r ${tier.color} text-white font-medium text-sm tracking-wider mb-4`}>
                  {tier.name}
                </div>
                <h2 className={`text-2xl md:text-3xl font-light mb-4 ${tier.textColor}`}>
                  {tier.tagline}
                </h2>
              </div>

              {/* Image */}
              {tier.image && (
                <div className="mb-8 text-center">
                  <img 
                    src={tier.image} 
                    alt={`${tier.name} visual`}
                    className="mx-auto rounded-2xl shadow-lg max-w-full h-auto max-h-96 object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Description */}
              <div className={`prose prose-lg max-w-none mb-8 ${tier.textColor}`}>
                <p className="text-lg leading-relaxed mb-6">
                  {tier.description}
                </p>
                <p className="text-base leading-relaxed mb-6">
                  {tier.startText}
                </p>
                {tier.additionalText && (
                  <p className="text-base leading-relaxed mb-6">
                    {tier.additionalText}
                  </p>
                )}
              </div>

              {/* Includes */}
              <div className="mb-8">
                <h3 className={`text-xl font-medium mb-4 ${tier.textColor}`}>
                  Your {tier.name.split(' ')[0]} Membership includes:
                </h3>
                <ul className="space-y-3">
                  {tier.includes.map((item, i) => (
                    <li key={i} className={`flex items-start space-x-3 ${tier.textColor}`}>
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${tier.color} mt-3 flex-shrink-0`}></div>
                      <span className="text-base leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Privileges */}
              {tier.privileges && (
                <div className="mb-8">
                  <h3 className={`text-xl font-medium mb-4 ${tier.textColor}`}>
                    {tier.name.split(' ')[0]} Member Privileges:
                  </h3>
                  <ul className="space-y-3">
                    {tier.privileges.map((privilege, i) => (
                      <li key={i} className={`flex items-start space-x-3 ${tier.textColor}`}>
                        <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${tier.color} mt-3 flex-shrink-0`}></div>
                        <span className="text-base leading-relaxed">{privilege}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Closing Text for Elite */}
              {tier.closingText && (
                <div className={`prose prose-lg max-w-none mb-8 ${tier.textColor}`}>
                  <p className="text-base leading-relaxed italic">
                    {tier.closingText}
                  </p>
                </div>
              )}

              {/* CTA Button */}
              <div className="text-center">
                <button
                  onClick={() => tier.id === 'elite' ? null : onNavigate('appointment-booking')}
                  className={`inline-flex items-center px-8 py-3 rounded-full font-medium text-white bg-gradient-to-r ${tier.color} hover:shadow-lg transform hover:scale-105 transition-all duration-200 ${
                    tier.id === 'elite' ? 'cursor-default opacity-75' : 'hover:shadow-xl'
                  }`}
                  disabled={tier.id === 'elite'}
                >
                  {tier.cta}
                  {tier.id !== 'elite' && (
                    <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="text-center mt-16 py-12 bg-gradient-to-r from-[#C8A25A]/10 to-[#B88E35]/10 rounded-2xl">
          <h2 className="text-2xl md:text-3xl font-light text-gray-900 mb-6">
            Ready to Begin Your Journey?
          </h2>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Schedule a consultation to discover which membership tier aligns with your wellness goals and lifestyle.
          </p>
          <button
            onClick={() => onNavigate('appointment-booking')}
            className="ka-button-primary text-lg px-8 py-4"
          >
            Book Your Discovery Session
          </button>
        </div>
      </div>
    </div>
  );
};

export default Membership;