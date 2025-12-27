<?php

namespace App\Filament\Widgets;

use App\Models\Submission;
use Filament\Widgets\ChartWidget;
use Flowframe\Trend\Trend;
use Flowframe\Trend\TrendValue;
use Illuminate\Support\Facades\Auth;

class SubmissionChart extends ChartWidget
{
    protected static ?string $heading = 'Grafik Pengajuan Mahasiswa';
    protected static ?int $sort = 2;
    protected int | string | array $columnSpan = 'full';

    public static function canView(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    protected function getData(): array
    {
        // --- PERBAIKAN: Ubah cara query data ---

        // 1. Ambil data untuk pengajuan yang 'Submitted'
        $submittedData = Trend::query(Submission::where('status', 'Submitted'))
            ->between(
                start: now()->startOfYear(),
                end: now()->endOfYear(),
            )
            ->perMonth()
            ->count();

        // 2. Ambil data untuk pengajuan yang 'Verified'
        $verifiedData = Trend::query(Submission::where('status', 'Verified'))
            ->between(
                start: now()->startOfYear(),
                end: now()->endOfYear(),
            )
            ->perMonth()
            ->count();

        return [
            'datasets' => [
                [
                    'label' => 'Disetujui (Verified)',
                    'data' => $verifiedData->map(fn(TrendValue $value) => $value->aggregate),
                    'borderColor' => '#16a34a', // hijau
                    'backgroundColor' => 'rgba(22,163,74,0.6)',
                    'fill' => true,
                ],
                [
                    'label' => 'Diajukan (Submitted)',
                    'data' => $submittedData->map(fn(TrendValue $value) => $value->aggregate),
                    'borderColor' => '#f59e0b', // kuning
                    'backgroundColor' => 'rgba(245,158,11,0.5)',
                    'fill' => true,
                ],
            ],
            'labels' => $submittedData->map(fn(TrendValue $value) => date('M', strtotime($value->date))),
        ];
    }

    protected function getType(): string
    {
        return 'line';
    }

    protected function getOptions(): array
    {
        return [
            'maintainAspectRatio' => false,
            'scales' => [
                'y' => [
                    'beginAtZero' => true,
                    'stacked' => true, // <-- Kunci untuk membuat stacked chart
                    'grid' => [
                        'color' => 'rgba(0,0,0,0.05)',
                    ],
                ],
                'x' => [
                    'stacked' => true, // <-- Kunci untuk membuat stacked chart
                    'grid' => [
                        'display' => false,
                    ],
                ],
            ],
            'plugins' => [
                'legend' => [
                    'display' => true,
                ],
                'tooltip' => [
                    'mode' => 'index',
                    'intersect' => false,
                ],
            ],
            'animation' => [
                'duration' => 1000,
            ],
        ];
    }
}
