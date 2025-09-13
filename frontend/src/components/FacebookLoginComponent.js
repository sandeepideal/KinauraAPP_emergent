import React, { useState } from 'react';
// import FacebookLogin from 'react-facebook-login/dist/facebook-login-render-props';

const FacebookLoginComponent = ({ onAuthSuccess, onAuthError }) => {
  const [isLoading, setIsLoading] = useState(false);

  const responseFacebook = async (response) => {
    if (response.accessToken) {
      setIsLoading(true);
      try {
        // Send Facebook access token to FastAPI backend for verification
        const backendResponse = await fetch('/api/auth/facebook', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_token: response.accessToken,
            user_id: response.userID,
            signed_request: response.signedRequest,
            user_data: {
              name: response.name,
              email: response.email,
              picture: response.picture?.data?.url
            }
          }),
        });

        if (backendResponse.ok) {
          const { access_token, user_info } = await backendResponse.json();
          onAuthSuccess({ token: access_token, user: user_info });
        } else {
          const errorData = await backendResponse.json();
          throw new Error(errorData.detail || 'Backend authentication failed');
        }
      } catch (error) {
        console.error('Facebook authentication error:', error);
        onAuthError(error);
      } finally {
        setIsLoading(false);
      }
    } else {
      console.error('Facebook login failed:', response);
      onAuthError(new Error(response.status || 'Facebook login failed'));
    }
  };

  return (
    <></>
    // <FacebookLogin
    //   appId={process.env.REACT_APP_FACEBOOK_APP_ID}
    //   autoLoad={false}
    //   fields="name,email,picture"
    //   scope="public_profile,email"
    //   callback={responseFacebook}
    //   render={renderProps => (
    //     <button
    //       onClick={renderProps.onClick}
    //       disabled={isLoading || renderProps.isDisabled}
    //       className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50 transition-colors"
    //     >
    //       <svg className="w-5 h-5 mr-2" fill="#1877F2" viewBox="0 0 24 24">
    //         <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    //       </svg>
    //       {isLoading ? 'Authenticating...' : 'Continue with Facebook'}
    //     </button>
    //   )}
    // />
  );
};

export default FacebookLoginComponent;