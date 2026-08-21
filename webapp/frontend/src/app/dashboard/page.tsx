export default function DashboardOverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-muted-foreground mt-2">
          Welcome to your language identification dashboard.
        </p>
      </div>
      <div className="text-muted-foreground">
        Go to the Documents tab to upload and manage your files.
      </div>
    </div>
  );
}
