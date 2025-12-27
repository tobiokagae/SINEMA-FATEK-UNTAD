<?php

namespace App\Filament\Widgets;

use App\Models\Student;
use App\Models\Submission;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Auth;

class StatsOverview extends BaseWidget
{
    public static function canView(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    protected function getStats(): array
    {
        return [
            Stat::make('Pengajuan Perlu Diverifikasi', Submission::where('status', 'Submitted')->count())
                ->description('Jumlah pengajuan yang menunggu validasi')
                ->descriptionIcon('heroicon-m-clock')
                ->color('warning'),
            Stat::make('Total Pengajuan Terverifikasi', Submission::where('status', 'Verified')->count())
                ->description('Semua pengajuan yang telah divalidasi')
                ->descriptionIcon('heroicon-m-check-badge')
                ->color('success'),
            Stat::make('Total Mahasiswa Terdaftar', Student::count())
                ->description('Jumlah mahasiswa di dalam sistem')
                ->descriptionIcon('heroicon-m-users')
                ->color('info'),
        ];
    }
}
