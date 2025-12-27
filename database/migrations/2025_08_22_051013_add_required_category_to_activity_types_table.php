<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('activity_types', function (Blueprint $table) {
            // Kolom ini akan kita gunakan untuk menandai kegiatan wajib
            // Contoh isinya: 'PKKMB', 'BAKTI_LINGKUNGAN', atau null jika tidak wajib.
            $table->string('required_category')->nullable()->after('score');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('activity_types', function (Blueprint $table) {
            $table->dropColumn('required_category');
        });
    }
};
