import { Cloud, Sun, CloudRain, CloudSnow, Wind } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, WeatherData } from '@/lib/api';

const WeatherWidget = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<WeatherData>({
    temperature: 0,
    condition: '',
    humidity: 0,
    windSpeed: 0,
    icon: '',
    location: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getApproxLocation = async () => {
      const res = await fetch('https://ipwhois.app/json/');
      const data = await res.json();

      return {
        latitude: data.latitude,
        longitude: data.longitude,
        city: data.city,
      };
    };

    const getLocation = async (
      callback: (location: {
        latitude: number;
        longitude: number;
        city: string;
      }) => void,
    ) => {
      callback(await getApproxLocation());
    };

    getLocation(async (location) => {
      try {
        const weatherData = await api.weather.getWeather({
          lat: location.latitude,
          lng: location.longitude,
        });

        setData({
          ...weatherData,
          location: location.city,
        });
      } catch (error) {
        console.error('Error fetching weather data:', error);
      } finally {
        setLoading(false);
      }
    });
  }, []);

  return (
    <div className="bg-light-secondary dark:bg-dark-secondary rounded-xl border border-light-200 dark:border-dark-200 shadow-sm flex flex-row items-center w-full h-24 min-h-[96px] max-h-[96px] px-3 py-2 gap-3">
      {loading ? (
        <div className="flex items-center justify-center w-full">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-light-200 dark:border-dark-200" />
        </div>
      ) : (
        <>
          <div className="flex flex-col items-start justify-center gap-1">
            <span className="text-sm text-black/50 dark:text-white/50">
              {data.location}
            </span>
            <div className="flex flex-row items-center gap-2">
              <span className="text-2xl font-medium">
                {Math.round(data.temperature)}°C
              </span>
              <span className="text-sm text-black/50 dark:text-white/50">
                {data.condition}
              </span>
            </div>
          </div>
          <div className="flex flex-row items-center gap-4 ml-auto">
            <div className="flex flex-row items-center gap-1">
              <Wind size={15} className="text-black/50 dark:text-white/50" />
              <span className="text-sm text-black/50 dark:text-white/50">
                {Math.round(data.windSpeed)} km/h
              </span>
            </div>
            <div className="flex flex-row items-center gap-1">
              <Cloud size={15} className="text-black/50 dark:text-white/50" />
              <span className="text-sm text-black/50 dark:text-white/50">
                {data.humidity}%
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default WeatherWidget;
