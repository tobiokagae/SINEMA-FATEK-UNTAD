<?php

use App\Http\Controllers\TranscriptController;
use Illuminate\Support\Facades\Route;

Route::view('/', 'welcome');

Route::middleware('auth')->group(function () {
    Route::get('students/{student}/transcript/{transcriptRequest?}', [TranscriptController::class, 'generate'])
        ->name('transcript.generate');

    Route::get('transcript-requests/{transcriptRequest}/preview', [TranscriptController::class, 'preview'])
        ->name('transcript.preview');
});

