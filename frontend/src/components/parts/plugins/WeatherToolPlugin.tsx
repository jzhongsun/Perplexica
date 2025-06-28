'use client';

import React, { useState } from 'react';
import { 
  Cloud, 
  Sun, 
  CloudRain, 
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  Thermometer,
  Droplets,
  Wind
} from 'lucide-react';
import { PartPlugin, PartRendererProps, PartRenderResult } from './index';

const WeatherToolRenderer: React.FC<{ part: any }> = ({ part }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const getStateIcon = () => {
    switch (part.state) {
      case 'input-streaming':
        return <Loader2 className="animate-spin" size={16} />;
      case 'input-available':
        return <Clock size={16} />;
      case 'output-available':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'output-error':
        return <XCircle size={16} className="text-red-500" />;
      default:
        return <Cloud size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Getting weather...';
      case 'input-available':
        return 'Location received';
      case 'output-available':
        return 'Weather data ready';
      case 'output-error':
        return 'Weather unavailable';
      default:
        return 'Ready';
    }
  };

  const getWeatherIcon = (condition: string) => {
    const lowerCondition = condition?.toLowerCase() || '';
    if (lowerCondition.includes('rain') || lowerCondition.includes('shower')) {
      return <CloudRain size={20} className="text-blue-500" />;
    } else if (lowerCondition.includes('sun') || lowerCondition.includes('clear')) {
      return <Sun size={20} className="text-yellow-500" />;
    } else {
      return <Cloud size={20} className="text-gray-500" />;
    }
  };

  const renderWeatherData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No weather data available</div>;
    }

    const weather = part.output;
    
    return (
      <div className="space-y-4">
        {/* 主要天气信息 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              {getWeatherIcon(weather.condition || weather.description)}
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                  {weather.location || weather.city || 'Unknown Location'}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {weather.condition || weather.description || 'No description'}
                </p>
              </div>
            </div>
            {weather.temperature && (
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {weather.temperature}°
                </div>
                {weather.feels_like && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Feels like {weather.feels_like}°
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* 详细信息 */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            {weather.humidity && (
              <div className="flex items-center space-x-2">
                <Droplets size={16} className="text-blue-500" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {weather.humidity}%
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Humidity
                  </div>
                </div>
              </div>
            )}
            
            {weather.wind_speed && (
              <div className="flex items-center space-x-2">
                <Wind size={16} className="text-gray-500" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {weather.wind_speed} km/h
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Wind
                  </div>
                </div>
              </div>
            )}
            
            {(weather.high || weather.low) && (
              <div className="flex items-center space-x-2">
                <Thermometer size={16} className="text-red-500" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {weather.high}° / {weather.low}°
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    High / Low
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* 预报信息 */}
        {weather.forecast && Array.isArray(weather.forecast) && (
          <div>
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Forecast:
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {weather.forecast.slice(0, 3).map((day: any, index: number) => (
                <div 
                  key={index}
                  className="bg-white dark:bg-gray-800 rounded p-3 border border-gray-200 dark:border-gray-600"
                >
                  <div className="text-xs font-medium text-gray-900 dark:text-gray-100 mb-1">
                    {day.date || day.day || `Day ${index + 1}`}
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      {getWeatherIcon(day.condition || day.description)}
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {day.condition || day.description}
                      </span>
                    </div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {day.high}°/{day.low}°
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="border border-sky-200 dark:border-sky-700 rounded-lg p-4 bg-sky-50 dark:bg-sky-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Weather
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {part.state === 'output-available' && part.output && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-sky-200 dark:hover:bg-sky-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      {part.input?.location && (
        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          <strong>Location:</strong> {part.input.location}
        </div>
      )}
      
      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderWeatherData()}
        </div>
      )}
    </div>
  );
};

export const WeatherToolPlugin: PartPlugin = {
  type: 'tool-weather',
  displayName: 'Weather',
  description: 'Renders weather tool calls and forecast data',
  canHandle: (partType: string) => partType === 'tool-weather' || partType === 'tool-get_weather',
  renderer: ({ part }: PartRendererProps): PartRenderResult => {
    return {
      shouldRender: true,
      content: <WeatherToolRenderer part={part} />
    };
  }
}; 