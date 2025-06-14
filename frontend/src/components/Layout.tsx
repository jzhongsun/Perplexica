const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <main className="pt-12 md:pt-12 bg-light-primary dark:bg-dark-primary min-h-screen">
      <div className="max-w-screen-lg mx-auto px-4">{children}</div>
    </main>
  );
};

export default Layout;
