import React, { useState, useEffect } from 'react';

const LongevityScoreboard = ({ user, onNavigate, onLogoClick }) => {
  const [myScore, setMyScore] = useState(null);
  const [leaderboard, setLeaderboard] = useState({ entries: [], total: 0 });
  const [cohorts, setCohorts] = useState([]);
  const [selectedCohort, setSelectedCohort] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Configuration - Use Supabase backend for longevity features
  const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL;
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (user) {
      fetchMyScore();
      fetchCohorts();
      fetchLeaderboard();
    }
  }, [user, selectedCohort, page]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchMyScore = async () => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/my`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setMyScore(data);
      } else if (response.status === 404) {
        // No biological age measurement yet
        setMyScore(null);
      } else {
        throw new Error('Failed to fetch score');
      }
    } catch (err) {
      console.error('Error fetching my score:', err);
      setMyScore(null);
    }
  };

  const fetchCohorts = async () => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/cohorts`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setCohorts(data.cohorts || []);
      }
    } catch (err) {
      console.error('Error fetching cohorts:', err);
    }
  };

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });

      if (selectedCohort) {
        params.append('cohort_key', selectedCohort);
      }

      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/leaderboard?${params}`);

      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data);
      } else {
        throw new Error('Failed to fetch leaderboard');
      }
    } catch (err) {
      console.error('Error fetching leaderboard:', err);
      setError('Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const handleCohortChange = (cohortKey) => {
    setSelectedCohort(cohortKey);
    setPage(1); // Reset to first page when changing cohort
  };

  const renderScore = (score) => {
    const getScoreColor = (score) => {
      if (score >= 80) return 'text-green-600';
      if (score >= 60) return 'text-yellow-600';
      if (score >= 40) return 'text-orange-600';
      return 'text-red-600';
    };

    return (
      <span className={`font-bold text-2xl ${getScoreColor(score)}`}>
        {Math.round(score)}
      </span>
    );
  };

  const renderDisplayInfo = (display) => {
    switch (display.mode) {
      case 'name':
        return (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gold bg-opacity-20 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium">
                {display.name ? display.name.charAt(0) : '?'}
              </span>
            </div>
            <span className="font-medium">{display.name || 'Unknown'}</span>
          </div>
        );
      case 'avatar':
        return (
          <div className="flex items-center space-x-2">
            {display.avatar_url ? (
              <img 
                src={display.avatar_url} 
                alt="Avatar" 
                className="w-8 h-8 rounded-full object-cover"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNGM0Y0RjYiLz4KPHBhdGggZD0iTTE2IDlDMTMuNzkgOSAxMiAxMC43OSAxMiAxM0MxMiAxNS4yMSAxMy43OSAxNyAxNiAxN0MxOC4yMSAxNyAyMCAxNS4yMSAyMCAxM0MyMCAxMC43OSAxOC4yMSA5IDE2IDlaTTE2IDE5QzEyLjY3IDE5IDYgMjAuNjcgNiAyNFYyNkgyNlYyNEMyNiAyMC42NyAxOS4zMyAxOSAxNiAxOVoiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+';
                }}
              />
            ) : (
              <div className="w-8 h-8 bg-gold bg-opacity-20 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium">
                  {display.name ? display.name.charAt(0) : '?'}
                </span>
              </div>
            )}
            <span className="font-medium">{display.name || 'Unknown'}</span>
          </div>
        );
      case 'anonymous':
        return (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">?</span>
            </div>
            <span className="font-medium italic">{display.handle || 'Anonymous'}</span>
          </div>
        );
      default:
        return <span className="font-medium italic">Unknown</span>;
    }
  };

  if (loading && !leaderboard.entries.length) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold mx-auto mb-4"></div>
          <p className="text-gray-600">Loading longevity scoreboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="app-header">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('dashboard'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="kinaura-logo-text hover:text-gold transition-colors">KinAura</span>
        </div>
        <button 
          onClick={() => onNavigate('menu')}
          className="hamburger-menu"
        >
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Page Title */}
        <div className="text-center">
          <h1 className="text-2xl kinaura-heading mb-2">Longevity Scoreboard</h1>
          <p className="text-gray-600 text-sm kinaura-body">Track your biological age advantage</p>
        </div>

        {/* My Score Card */}
        {myScore ? (
          <div className="cream-card">
            <h2 className="text-lg font-medium mb-4 kinaura-subheading">Your Longevity Score</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-gold mb-1">{Math.round(myScore.score)}</div>
                <div className="text-sm text-gray-600 kinaura-body">Score</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-charcoal mb-1">#{myScore.rank}</div>
                <div className="text-sm text-gray-600 kinaura-body">Rank</div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 kinaura-body">Chronological Age:</span>
                <div className="font-medium">{myScore.chronological_age_years.toFixed(1)} years</div>
              </div>
              <div>
                <span className="text-gray-600 kinaura-body">Biological Age:</span>
                <div className="font-medium">{myScore.biological_age_years.toFixed(1)} years</div>
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-gold bg-opacity-10 rounded-lg">
              <div className="text-center">
                <div className="font-medium text-sm">
                  You are {Math.abs(myScore.delta_years).toFixed(1)} years{' '}
                  <span className={myScore.delta_years > 0 ? 'text-green-600' : 'text-red-600'}>
                    {myScore.delta_years > 0 ? 'younger' : 'older'}
                  </span>{' '}
                  biologically
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Cohort: {myScore.total_in_cohort} patients
                </div>
              </div>
            </div>

            {/* Neighbors */}
            {myScore.neighbors && myScore.neighbors.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium mb-2 kinaura-body">Your Position</h3>
                <div className="space-y-2">
                  {myScore.neighbors.map((neighbor, index) => (
                    <div 
                      key={index}
                      className={`flex items-center justify-between p-2 rounded ${
                        neighbor.is_current_patient ? 'bg-gold bg-opacity-20' : 'bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium w-8">#{neighbor.rank}</span>
                        {renderDisplayInfo(neighbor.display)}
                      </div>
                      <div className="flex items-center space-x-2">
                        {renderScore(neighbor.score)}
                        {neighbor.is_current_patient && (
                          <span className="text-xs text-gold font-medium">YOU</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="cream-card text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2 kinaura-subheading">No Score Available</h3>
            <p className="text-gray-600 text-sm mb-4 kinaura-body">
              A biological age measurement is required to calculate your longevity score.
            </p>
            <button 
              onClick={() => onNavigate('services')}
              className="pill-button"
            >
              Book Assessment
            </button>
          </div>
        )}

        {/* Cohort Filter */}
        {cohorts.length > 0 && (
          <div className="cream-card">
            <h3 className="text-lg font-medium mb-3 kinaura-subheading">Filter by Group</h3>
            <div className="grid grid-cols-1 gap-2">
              <button
                onClick={() => handleCohortChange('')}
                className={`p-3 rounded-lg text-left transition-colors ${
                  selectedCohort === '' ? 'bg-gold bg-opacity-20 border border-gold' : 'bg-white border border-gray-200'
                }`}
              >
                <div className="font-medium text-sm">All Patients</div>
                <div className="text-xs text-gray-600">
                  {leaderboard.total} total entries
                </div>
              </button>
              {cohorts.map((cohort) => (
                <button
                  key={cohort.cohort_key}
                  onClick={() => handleCohortChange(cohort.cohort_key)}
                  className={`p-3 rounded-lg text-left transition-colors ${
                    selectedCohort === cohort.cohort_key ? 'bg-gold bg-opacity-20 border border-gold' : 'bg-white border border-gray-200'
                  }`}
                >
                  <div className="font-medium text-sm">{cohort.description}</div>
                  <div className="text-xs text-gray-600">
                    {cohort.patient_count} patients • avg score {cohort.avg_score}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Leaderboard */}
        <div className="cream-card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium kinaura-subheading">Leaderboard</h3>
            <div className="text-xs text-gray-600">
              {selectedCohort ? `${leaderboard.total} in group` : `${leaderboard.total} total`}
            </div>
          </div>

          {error && (
            <div className="text-center py-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {!error && leaderboard.entries.length === 0 && !loading && (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-gray-600 text-sm">No entries available</p>
            </div>
          )}

          {leaderboard.entries.length > 0 && (
            <div className="space-y-2">
              {leaderboard.entries.map((entry, index) => (
                <div 
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    entry.pinned ? 'border-gold bg-gold bg-opacity-10' : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <div className={`text-lg font-bold w-8 ${
                      entry.rank === 1 ? 'text-yellow-500' :
                      entry.rank === 2 ? 'text-gray-400' :
                      entry.rank === 3 ? 'text-yellow-700' : 'text-gray-600'
                    }`}>
                      {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                    </div>
                    {renderDisplayInfo(entry.display)}
                    {entry.pinned && (
                      <span className="text-xs bg-gold text-white px-2 py-1 rounded-full">
                        FEATURED
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    {renderScore(entry.score)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {leaderboard.total > pageSize && (
            <div className="flex justify-between items-center mt-6">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className={`pill-button text-sm ${page === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                Previous
              </button>
              
              <div className="text-sm text-gray-600">
                Page {page} of {Math.ceil(leaderboard.total / pageSize)}
              </div>
              
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(leaderboard.total / pageSize)}
                className={`pill-button text-sm ${
                  page >= Math.ceil(leaderboard.total / pageSize) ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Buttons */}
      <button 
        onClick={() => onNavigate('concierge')}
        className="floating-action floating-chat"
      >
        <span className="text-lg">💬</span>
      </button>
      <button 
        onClick={() => onNavigate('services')}
        className="floating-action floating-calendar"
      >
        <span className="text-lg">📊</span>
      </button>
    </div>
  );
};

export default LongevityScoreboard;