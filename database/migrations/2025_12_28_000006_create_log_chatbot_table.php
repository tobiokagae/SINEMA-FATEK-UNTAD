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
        Schema::create('log_chatbot', function (Blueprint $table) {
            $table->id();
            $table->string('session_id', 50);
            $table->string('role', 20);
            $table->text('content');
            $table->json('sources')->nullable();
            $table->float('latency')->nullable();
            $table->boolean('cached')->default(false);
            $table->timestamps();

            $table->foreign('session_id')->references('id')->on('sessions_chatbot')->onDelete('cascade');
            $table->index('session_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('log_chatbot');
    }
};
