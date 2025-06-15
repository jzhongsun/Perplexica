'use client';

import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';

export default function MetadataProvider() {
  const { t } = useTranslation();

  useEffect(() => {
    document.title = t('metadata.title');
    document.querySelector('meta[name="description"]')?.setAttribute('content', t('metadata.description'));
  }, [t]);

  return null;
} 