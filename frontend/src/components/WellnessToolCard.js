import React from 'react';

const WellnessToolCard = ({ 
  onClick, 
  icon, 
  title, 
  className = "",
  iconClassName = "",
  ...props 
}) => {
  return (
    <button 
      onClick={onClick}
      className={`ka-wellness-card group ${className}`}
      {...props}
    >
      <div className="ka-wellness-card__icon">
        {icon}
      </div>
      <h4 className="ka-wellness-card__title">{title}</h4>
    </button>
  );
};

export default WellnessToolCard;