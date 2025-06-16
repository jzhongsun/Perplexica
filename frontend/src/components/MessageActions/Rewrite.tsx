import { Pencil } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const Rewrite = ({
  rewrite,
  messageId,
}: {
  rewrite: (messageId: string) => void;
  messageId: string;
}) => {
  const { t } = useTranslation();

  return (
    <button
      onClick={() => rewrite(messageId)}
      className="p-2 text-black/70 dark:text-white/70 rounded-xl hover:bg-light-secondary dark:hover:bg-dark-secondary transition duration-200 hover:text-black dark:hover:text-white"
      title={t('chat.message.rewrite')}
    >
      <Pencil size={18} />
    </button>
  );
};

export default Rewrite;
